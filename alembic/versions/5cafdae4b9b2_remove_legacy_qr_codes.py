"""remove legacy qr codes

Revision ID: 5cafdae4b9b2
Revises: 61ca11298945
Create Date: 2026-10-16 15:37:16.266659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cafdae4b9b2'
down_revision: Union[str, Sequence[str], None] = '473ba9352566'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("qr_codes")

def downgrade() -> None:
    op.create_table(
        "qr_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("used_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "points > 0",
            name="check_qr_points_positive",
        ),
        sa.ForeignKeyConstraint(
            ["used_by_user_id"],
            ["users.id"],
            name="fk_qr_codes_used_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_qr_codes_token",
        "qr_codes",
        ["token"],
        unique=True,
    )
