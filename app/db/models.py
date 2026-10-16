from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "points >= 0",
            name="check_user_points_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Данные гостя по ТЗ
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Внутренний случайный идентификатор персонального пропуска.
    # Позже именно его будем подписывать HMAC.
    pass_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # None = гость ещё не отмечен на мероприятии
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="check_point_transaction_amount_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Кому начислили
    guest_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Кто начислил
    organizer_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # Сколько
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # За что
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Когда
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
