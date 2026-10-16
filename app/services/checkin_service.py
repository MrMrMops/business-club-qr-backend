from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import PointTransaction, User


class GuestNotFoundError(Exception):
    pass


class AlreadyCheckedInError(Exception):
    pass


async def check_in_guest(
    session: AsyncSession,
    guest_id: int,
    organizer_telegram_id: int,
):
    async with session.begin():
        result = await session.execute(
            update(User)
            .where(
                User.id == guest_id,
                User.checked_in_at.is_(None),
            )
            .values(
                checked_in_at=func.now(),
                points=User.points + settings.checkin_points,
            )
            .returning(
                User.id,
                User.name,
                User.points,
                User.checked_in_at,
            )
        )

        guest = result.first()

        if guest is None:
            existing_result = await session.execute(
                select(User.id).where(User.id == guest_id)
            )

            existing_guest = existing_result.scalar_one_or_none()

            if existing_guest is None:
                raise GuestNotFoundError()

            raise AlreadyCheckedInError()

        guest_id, guest_name, new_balance, checked_in_at = guest

        transaction = PointTransaction(
            guest_id=guest_id,
            organizer_telegram_id=organizer_telegram_id,
            amount=settings.checkin_points,
            reason="event_checkin",
        )

        session.add(transaction)

    return {
        "guest_id": guest_id,
        "guest_name": guest_name,
        "points_added": settings.checkin_points,
        "balance": new_balance,
        "checked_in_at": checked_in_at,
    }