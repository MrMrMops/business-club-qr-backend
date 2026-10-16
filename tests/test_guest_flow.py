import asyncio

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.db.models import PointTransaction, User
from app.services.checkin_service import (
    AlreadyCheckedInError,
    check_in_guest,
)
from app.services.guest_service import (
    GuestAlreadyExistsError,
    create_guest,
    get_guest_by_pass_token,
)
from app.services.pass_token_service import (
    create_pass_token,
    verify_pass_token,
)
from app.services.qr_decode_service import decode_qr_image
from app.services.qr_image_service import generate_qr_image


@pytest.mark.asyncio
async def test_create_guest(session):
    guest = await create_guest(
        session=session,
        name="Nikita Shestakov",
        category="guest",
        telegram_id=123456789,
        username="MrMops",
    )

    assert guest.id is not None
    assert guest.name == "Nikita Shestakov"
    assert guest.category == "guest"
    assert guest.telegram_id == 123456789
    assert guest.points == 0
    assert guest.pass_id
    assert guest.checked_in_at is None


@pytest.mark.asyncio
async def test_guest_telegram_id_must_be_unique(session):
    await create_guest(
        session=session,
        name="First Guest",
        category="guest",
        telegram_id=123456789,
    )

    with pytest.raises(GuestAlreadyExistsError):
        await create_guest(
            session=session,
            name="Second Guest",
            category="vip",
            telegram_id=123456789,
        )


def test_pass_token_is_valid():
    token = create_pass_token("test-pass-id")

    assert verify_pass_token(token) == "test-pass-id"


def test_tampered_pass_token_is_invalid():
    token = create_pass_token("test-pass-id")

    tampered_token = token.replace(
        "test-pass-id",
        "another-pass-id",
    )

    assert verify_pass_token(tampered_token) is None


@pytest.mark.asyncio
async def test_guest_can_be_found_by_signed_token(session):
    guest = await create_guest(
        session=session,
        name="Nikita Shestakov",
        category="guest",
        telegram_id=123456789,
    )

    token = create_pass_token(guest.pass_id)

    found_guest = await get_guest_by_pass_token(
        session=session,
        token=token,
    )

    assert found_guest is not None
    assert found_guest.id == guest.id
    assert found_guest.telegram_id == 123456789


@pytest.mark.asyncio
async def test_checkin_awards_points_and_creates_history(session):
    guest = await create_guest(
        session=session,
        name="Nikita Shestakov",
        category="guest",
        telegram_id=123456789,
    )

    result = await check_in_guest(
        session=session,
        guest_id=guest.id,
        organizer_telegram_id=987654321,
    )

    assert result["points_added"] == settings.checkin_points
    assert result["balance"] == settings.checkin_points

    user_result = await session.execute(
        select(User).where(User.id == guest.id)
    )
    saved_guest = user_result.scalar_one()

    assert saved_guest.points == settings.checkin_points
    assert saved_guest.checked_in_at is not None

    transaction_result = await session.execute(
        select(PointTransaction).where(
            PointTransaction.guest_id == guest.id
        )
    )
    transaction = transaction_result.scalar_one()

    assert transaction.organizer_telegram_id == 987654321
    assert transaction.amount == settings.checkin_points
    assert transaction.reason == "event_checkin"
    assert transaction.created_at is not None


@pytest.mark.asyncio
async def test_guest_cannot_be_checked_in_twice(session):
    guest = await create_guest(
        session=session,
        name="Nikita Shestakov",
        category="guest",
        telegram_id=123456789,
    )

    guest_id = guest.id

    await check_in_guest(
        session=session,
        guest_id=guest_id,
        organizer_telegram_id=111,
    )

    with pytest.raises(AlreadyCheckedInError):
        await check_in_guest(
            session=session,
            guest_id=guest_id,
            organizer_telegram_id=222,
        )

    result = await session.execute(
        select(User).where(User.id == guest_id)
    )
    saved_guest = result.scalar_one()

    assert saved_guest.points == settings.checkin_points

    transactions = await session.execute(
        select(PointTransaction).where(
            PointTransaction.guest_id == guest_id
        )
    )

    assert len(transactions.scalars().all()) == 1

@pytest.mark.asyncio
async def test_concurrent_checkin_awards_points_once(
    session,
    session_factory,
):
    guest = await create_guest(
        session=session,
        name="Nikita Shestakov",
        category="guest",
        telegram_id=123456789,
    )

    async def checkin(organizer_id):
        async with session_factory() as concurrent_session:
            try:
                return await check_in_guest(
                    session=concurrent_session,
                    guest_id=guest.id,
                    organizer_telegram_id=organizer_id,
                )
            except AlreadyCheckedInError:
                return "already_checked_in"

    results = await asyncio.gather(
        checkin(111),
        checkin(222),
    )

    successful_results = [
        result
        for result in results
        if result != "already_checked_in"
    ]

    assert len(successful_results) == 1
    assert results.count("already_checked_in") == 1

    async with session_factory() as verification_session:
        user_result = await verification_session.execute(
            select(User).where(User.id == guest.id)
        )
        saved_guest = user_result.scalar_one()

        assert saved_guest.points == settings.checkin_points

        transaction_result = await verification_session.execute(
            select(PointTransaction).where(
                PointTransaction.guest_id == guest.id
            )
        )

        assert len(transaction_result.scalars().all()) == 1


def test_qr_image_can_be_generated_and_decoded():
    token = create_pass_token("test-pass-id")

    image = generate_qr_image(token)

    decoded_token = decode_qr_image(
        image.getvalue()
    )

    assert decoded_token == token
    assert verify_pass_token(decoded_token) == "test-pass-id"