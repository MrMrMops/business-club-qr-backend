from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine


router = APIRouter(
    tags=["Health"],
)


@router.get("/")
async def root():
    return {"status": "ok"}


@router.get("/db-check")
async def db_check():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))

    return {
        "database": "ok",
        "result": result.scalar(),
    }