from typing import Optional

from pydantic import BaseModel, Field


class GuestCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    telegram_id: int

    username: Optional[str] = None


class GuestResponse(BaseModel):
    id: int
    name: str
    category: str
    telegram_id: int
    username: Optional[str] = None
    points: int