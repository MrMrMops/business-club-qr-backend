from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.schemas.guest import GuestCreate, GuestResponse
from app.services.guest_service import (
    GuestAlreadyExistsError,
    create_guest,
)


router = APIRouter(
    prefix="/guests",
    tags=["Guests"],
)


@router.post(
    "",
    response_model=GuestResponse,
    status_code=201,
)
async def create_guest_endpoint(
    data: GuestCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        guest = await create_guest(
            session=session,
            name=data.name,
            category=data.category,
            telegram_id=data.telegram_id,
            username=data.username,
        )

    except GuestAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Guest with this Telegram ID already exists",
        )

    return GuestResponse(
        id=guest.id,
        name=guest.name,
        category=guest.category,
        telegram_id=guest.telegram_id,
        username=guest.username,
        points=guest.points,
    )