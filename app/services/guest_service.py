import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.pass_token_service import verify_pass_token


class GuestAlreadyExistsError(Exception):
    pass


class GuestNotFoundError(Exception):
    pass


async def create_guest(
    session: AsyncSession,
    name: str,
    category: str,
    telegram_id: int,
    username: str = None,
) -> User:
    existing_result = await session.execute(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

    existing_guest = existing_result.scalar_one_or_none()

    if existing_guest is not None:
        raise GuestAlreadyExistsError()

    pass_id = secrets.token_urlsafe(32)

    guest = User(
        name=name,
        category=category,
        telegram_id=telegram_id,
        username=username,
        pass_id=pass_id,
        points=0,
    )

    session.add(guest)
    await session.commit()

    return guest


async def get_guest_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
):
    result = await session.execute(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )

    return result.scalar_one_or_none()


async def get_guest_by_pass_token(
    session: AsyncSession,
    token: str,
):
    pass_id = verify_pass_token(token)

    if pass_id is None:
        return None

    result = await session.execute(
        select(User).where(
            User.pass_id == pass_id
        )
    )

    return result.scalar_one_or_none()