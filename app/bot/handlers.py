from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import User
from app.services.qr_service import (
    QRAlreadyUsedError,
    QRNotFoundError,
    redeem_qr,
)


router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    command: CommandObject,
):
    token = command.args

    # Обычный /start без QR
    if not token:
        await message.answer(
            "Привет! Здесь можно получать баллы за QR-коды.\n\n"
            "Используй QR-код или команду /balance, "
            "чтобы посмотреть баланс."
        )
        return

    if message.from_user is None:
        return

    async with SessionLocal() as session:
        try:
            result = await redeem_qr(
                session=session,
                token=token,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )

        except QRNotFoundError:
            await message.answer(
                "QR-код недействителен."
            )
            return

        except QRAlreadyUsedError:
            await message.answer(
                "Этот QR-код уже был использован."
            )
            return

    await message.answer(
        f"Начислено: {result['points_added']} баллов.\n"
        f"Текущий баланс: {result['balance']}."
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
            "У тебя пока нет начисленных баллов."
        )
        return

    await message.answer(
        f"Твой баланс: {user.points} баллов."
    )