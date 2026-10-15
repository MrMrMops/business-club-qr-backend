import secrets

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QRCode, User


class QRNotFoundError(Exception):
    pass


class QRAlreadyUsedError(Exception):
    pass


async def create_qr(
    session: AsyncSession,
    points: int,
) -> QRCode:
    token = secrets.token_urlsafe(32)

    qr = QRCode(
        token=token,
        points=points,
    )

    session.add(qr)

    await session.commit()

    return qr


async def redeem_qr(
    session: AsyncSession,
    token: str,
    telegram_id: int,
    username: str = None,
):
    async with session.begin():

        # Создаём пользователя, если его ещё нет.
        # Если пользователь уже существует — ничего не делаем.
        statement = (
            insert(User)
            .values(
                telegram_id=telegram_id,
                username=username,
                points=0,
            )
            .on_conflict_do_nothing(
                index_elements=[User.telegram_id]
            )
        )

        await session.execute(statement)

        # Получаем пользователя
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one()

        # Пытаемся забрать QR.
        #
        # КЛЮЧЕВОЙ МОМЕНТ:
        # UPDATE произойдёт только если used_at IS NULL.
        qr_result = await session.execute(
            update(QRCode)
            .where(
                QRCode.token == token,
                QRCode.used_at.is_(None),
            )
            .values(
                used_by_user_id=user.id,
                used_at=func.now(),
            )
            .returning(
                QRCode.id,
                QRCode.points,
            )
        )

        qr = qr_result.first()

        if qr is None:
            existing_qr = await session.execute(
                select(QRCode).where(
                    QRCode.token == token
                )
            )

            existing_qr = existing_qr.scalar_one_or_none()

            if existing_qr is None:
                raise QRNotFoundError()

            raise QRAlreadyUsedError()

        qr_id, points = qr

        # Начисляем баллы атомарным UPDATE
        balance_result = await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                points=User.points + points
            )
            .returning(User.points)
        )

        new_balance = balance_result.scalar_one()

    return {
        "qr_id": qr_id,
        "points_added": points,
        "balance": new_balance,
    }