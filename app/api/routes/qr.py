from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_session
from app.schemas.qr import RedeemQRRequest
from app.services.qr_image_service import generate_qr_image
from app.services.qr_service import (
    QRAlreadyUsedError,
    QRNotFoundError,
    create_qr,
    redeem_qr,
)


router = APIRouter(
    prefix="/qr",
    tags=["QR"],
)


@router.post("")
async def create_qr_endpoint(
    points: int = Query(gt=0),
    session: AsyncSession = Depends(get_session),
):
    qr = await create_qr(
        session=session,
        points=points,
    )

    return {
        "id": qr.id,
        "token": qr.token,
        "points": qr.points,
    }


@router.post("/image")
async def create_qr_image_endpoint(
    points: int = Query(gt=0),
    session: AsyncSession = Depends(get_session),
):
    qr = await create_qr(
        session=session,
        points=points,
    )

    link = (
        f"https://t.me/{settings.telegram_bot_username}"
        f"?start={qr.token}"
    )

    image = generate_qr_image(link)

    return StreamingResponse(
        image,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="qr_{qr.id}.png"'
        },
    )


@router.post("/{token}/redeem")
async def redeem_qr_endpoint(
    token: str,
    data: RedeemQRRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await redeem_qr(
            session=session,
            token=token,
            telegram_id=data.telegram_id,
            username=data.username,
        )

    except QRNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="QR code not found",
        )

    except QRAlreadyUsedError:
        raise HTTPException(
            status_code=409,
            detail="QR code already used",
        )