from typing import Optional

from pydantic import BaseModel


class RedeemQRRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None