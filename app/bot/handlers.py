from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import select
from io import BytesIO

from app.services.qr_decode_service import decode_qr_image
from app.db.database import SessionLocal
from app.db.models import User
from app.services.guest_service import get_guest_by_telegram_id
from app.services.pass_token_service import create_pass_token
from app.services.qr_image_service import generate_qr_image

from aiogram.filters.command import CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.config import settings
from app.services.guest_service import get_guest_by_pass_token
from app.services.organizer_service import is_organizer

from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.services.checkin_service import (
    AlreadyCheckedInError,
    GuestNotFoundError,
    check_in_guest,
)

router = Router()

def build_guest_card(guest: User):
    if guest.checked_in_at is None:
        checkin_status = "❌ Ещё не отмечен"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=(
                            f"✅ Отметить приход "
                            f"+{settings.checkin_points}"
                        ),
                        callback_data=f"checkin:{guest.id}",
                    )
                ]
            ]
        )

    else:
        checkin_status = "✅ Приход уже отмечен"
        keyboard = None

    text = (
        "Карточка гостя\n\n"
        f"Имя: {guest.name}\n"
        f"Категория: {guest.category}\n"
        f"Telegram ID: {guest.telegram_id}\n"
        f"Баллы: {guest.points}\n"
        f"Приход: {checkin_status}"
    )

    return text, keyboard

@router.message(CommandStart())
async def start_handler(message: Message):
    if message.from_user is None:
        return

    await message.answer(
        "Привет!\n\n"
        "Команды:\n"
        "/qr — получить персональный QR-пропуск\n"
        "/balance — посмотреть количество баллов"
    )


@router.message(Command("qr"))
async def qr_handler(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        guest = await get_guest_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

    if guest is None:
        await message.answer(
            "Ты пока не зарегистрирован как гость мероприятия."
        )
        return

    token = create_pass_token(guest.pass_id)

    qr_image = generate_qr_image(token)

    photo = BufferedInputFile(
        qr_image.getvalue(),
        filename="personal_pass.png",
    )

    await message.answer_photo(
        photo=photo,
        caption=(
            "Твой персональный QR-пропуск.\n\n"
            f"Имя: {guest.name}\n"
            f"Категория: {guest.category}\n\n"
            "Покажи этот QR организатору на регистрации."
        ),
    )


@router.message(Command("balance"))
async def balance_handler(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

    if user is None:
        await message.answer(
            "Ты пока не зарегистрирован как гость мероприятия."
        )
        return

    await message.answer(
        f"Твой баланс: {user.points} баллов."
    )

@router.message(Command("check"))
async def check_guest_handler(
    message: Message,
    command: CommandObject,
):
    if message.from_user is None:
        return

    if not is_organizer(message.from_user.id):
        await message.answer(
            "Эта команда доступна только организаторам."
        )
        return

    token = command.args

    if not token:
        await message.answer(
            "Передай token после команды:\n\n"
            "/check TOKEN"
        )
        return

    async with SessionLocal() as session:
        guest = await get_guest_by_pass_token(
            session=session,
            token=token,
        )

    if guest is None:
        await message.answer(
            "Пропуск недействителен или гость не найден."
        )
        return

    if guest.checked_in_at is None:
        checkin_status = "❌ Ещё не отмечен"
    else:
        checkin_status = "✅ Приход уже отмечен"

    keyboard = None

    if guest.checked_in_at is None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=(
                            f"✅ Отметить приход "
                            f"+{settings.checkin_points}"
                        ),
                        callback_data=f"checkin:{guest.id}",
                    )
                ]
            ]
        )

    await message.answer(
        (
            "Карточка гостя\n\n"
            f"Имя: {guest.name}\n"
            f"Категория: {guest.category}\n"
            f"Telegram ID: {guest.telegram_id}\n"
            f"Баллы: {guest.points}\n"
            f"Приход: {checkin_status}"
        ),
        reply_markup=keyboard,
    )

@router.callback_query(lambda callback: callback.data.startswith("checkin:"))
async def checkin_callback(callback: CallbackQuery):
    if callback.from_user is None:
        return

    if not is_organizer(callback.from_user.id):
        await callback.answer(
            "Доступно только организаторам.",
            show_alert=True,
        )
        return

    if callback.data is None:
        return

    try:
        guest_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer(
            "Некорректные данные.",
            show_alert=True,
        )
        return

    async with SessionLocal() as session:
        try:
            result = await check_in_guest(
                session=session,
                guest_id=guest_id,
                organizer_telegram_id=callback.from_user.id,
            )

        except GuestNotFoundError:
            await callback.answer(
                "Гость не найден.",
                show_alert=True,
            )
            return

        except AlreadyCheckedInError:
            await callback.answer(
                "Приход этого гостя уже был отмечен.",
                show_alert=True,
            )
            return

    await callback.answer(
        "Приход отмечен, баллы начислены."
    )

    if callback.message is not None:
        await callback.message.edit_text(
            (
                "Карточка гостя\n\n"
                f"Имя: {result['guest_name']}\n"
                f"Баллы: {result['balance']}\n"
                "Приход: ✅ Отмечен\n\n"
                f"Начислено: +{result['points_added']} баллов"
            )
        )


@router.callback_query(lambda callback: callback.data.startswith("checkin:"))
async def checkin_callback(callback: CallbackQuery):
    if callback.from_user is None:
        return

    if not is_organizer(callback.from_user.id):
        await callback.answer(
            "Доступно только организаторам.",
            show_alert=True,
        )
        return

    if callback.data is None:
        return

    try:
        guest_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer(
            "Некорректные данные.",
            show_alert=True,
        )
        return

    async with SessionLocal() as session:
        try:
            result = await check_in_guest(
                session=session,
                guest_id=guest_id,
                organizer_telegram_id=callback.from_user.id,
            )

        except GuestNotFoundError:
            await callback.answer(
                "Гость не найден.",
                show_alert=True,
            )
            return

        except AlreadyCheckedInError:
            await callback.answer(
                "Приход этого гостя уже был отмечен.",
                show_alert=True,
            )
            return

    await callback.answer(
        "Приход отмечен, баллы начислены."
    )

    if callback.message is not None:
        await callback.message.edit_text(
            (
                "Карточка гостя\n\n"
                f"Имя: {result['guest_name']}\n"
                f"Баллы: {result['balance']}\n"
                "Приход: ✅ Отмечен\n\n"
                f"Начислено: +{result['points_added']} баллов"
            )
        )

@router.message(F.photo)
async def qr_photo_handler(message: Message):
    if message.from_user is None:
        return

    if not is_organizer(message.from_user.id):
        await message.answer(
            "Распознавание пропусков доступно только организаторам."
        )
        return

    photo = message.photo[-1]

    buffer = BytesIO()

    await message.bot.download(
        photo,
        destination=buffer,
    )

    image_bytes = buffer.getvalue()

    token = decode_qr_image(image_bytes)

    if token is None:
        await message.answer(
            "Не удалось распознать QR-код на фотографии.\n\n"
            "Попробуй сделать фото ближе или используй "
            "/check TOKEN."
        )
        return

    async with SessionLocal() as session:
        guest = await get_guest_by_pass_token(
            session=session,
            token=token,
        )

    if guest is None:
        await message.answer(
            "QR-код распознан, но пропуск недействителен."
        )
        return

    text, keyboard = build_guest_card(guest)

    await message.answer(
        text,
        reply_markup=keyboard,
    )

@router.message(Command("id"))
async def id_handler(message: Message):
    if message.from_user is None:
        return

    await message.answer(
        f"Твой Telegram ID: {message.from_user.id}"
    )