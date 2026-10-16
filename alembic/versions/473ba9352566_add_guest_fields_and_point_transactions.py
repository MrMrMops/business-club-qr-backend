"""add guest fields and point transactions

Revision ID: 473ba9352566
Revises: 640523385602
Create Date: 2026-10-16 14:30:54.634070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '473ba9352566'
down_revision: Union[str, Sequence[str], None] = '640523385602'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "pass_id",
            sa.String(length=255),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "checked_in_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_users_pass_id",
        "users",
        ["pass_id"],
        unique=True,
    )

    op.create_table(
        "point_transactions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "guest_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "organizer_telegram_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="check_point_transaction_amount_positive",
        ),
        sa.ForeignKeyConstraint(
            ["guest_id"],
            ["users.id"],
            name="fk_point_transactions_guest_id_users",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_point_transactions_guest_id",
        "point_transactions",
        ["guest_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_point_transactions_guest_id",
        table_name="point_transactions",
    )

    op.drop_table("point_transactions")

    op.drop_index(
        "ix_users_pass_id",
        table_name="users",
    )

    op.drop_column(
        "users",
        "checked_in_at",
    )

    op.drop_column(
        "users",
        "pass_id",
    )

    op.drop_column(
        "users",
        "category",
    )

    op.drop_column(
        "users",
        "name",
    )