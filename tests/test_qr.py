import asyncio

import pytest
from sqlalchemy import select

from app.db.models import QRCode, User
from app.services.qr_service import (
    QRAlreadyUsedError,
    create_qr,
    redeem_qr,
)


@pytest.mark.asyncio
async def test_create_qr(session):
    qr = await create_qr(
        session=session,
        points=100,
    )

    assert qr.id is not None
    assert qr.points == 100
    assert qr.token is not None
    assert qr.used_at is None

    result = await session.execute(
        select(QRCode).where(QRCode.id == qr.id)
    )

    saved_qr = result.scalar_one()

    assert saved_qr.points == 100
    assert saved_qr.token == qr.token


@pytest.mark.asyncio
async def test_redeem_qr(session):
    qr = await create_qr(
        session=session,
        points=100,
    )

    result = await redeem_qr(
        session=session,
        token=qr.token,
        telegram_id=123456789,
        username="nikita",
    )

    assert result["points_added"] == 100
    assert result["balance"] == 100

    user_result = await session.execute(
        select(User).where(
            User.telegram_id == 123456789
        )
    )

    user = user_result.scalar_one()

    assert user.points == 100


@pytest.mark.asyncio
async def test_qr_cannot_be_redeemed_twice(session):
    qr = await create_qr(
        session=session,
        points=100,
    )

    await redeem_qr(
        session=session,
        token=qr.token,
        telegram_id=123456789,
        username="nikita",
    )

    with pytest.raises(QRAlreadyUsedError):
        await redeem_qr(
            session=session,
            token=qr.token,
            telegram_id=123456789,
            username="nikita",
        )

    user_result = await session.execute(
        select(User).where(
            User.telegram_id == 123456789
        )
    )

    user = user_result.scalar_one()

    assert user.points == 100


@pytest.mark.asyncio
async def test_concurrent_redeem_only_awards_points_once(
    session,
    session_factory,
):
    qr = await create_qr(
        session=session,
        points=100,
    )

    user = User(
        telegram_id=123456789,
        username="nikita",
        points=0,
    )

    session.add(user)
    await session.commit()

    async def redeem():
        async with session_factory() as concurrent_session:
            try:
                return await redeem_qr(
                    session=concurrent_session,
                    token=qr.token,
                    telegram_id=123456789,
                    username="nikita",
                )

            except QRAlreadyUsedError:
                return "already_used"

    results = await asyncio.gather(
        redeem(),
        redeem(),
    )

    successful = [
        result
        for result in results
        if result != "already_used"
    ]

    failed = [
        result
        for result in results
        if result == "already_used"
    ]

    assert len(successful) == 1
    assert len(failed) == 1

    async with session_factory() as check_session:
        result = await check_session.execute(
            select(User).where(
                User.telegram_id == 123456789
            )
        )

        user = result.scalar_one()

        assert user.points == 100