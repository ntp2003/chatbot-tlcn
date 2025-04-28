"""add current filter and consultation status column to user_memory

Revision ID: ee9837b95476
Revises: b0b9ba1f513b
Create Date: 2025-04-19 20:24:24.778735

"""
# seventeenth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "ee9837b95476"
down_revision: Union[str, None] = "b0b9ba1f513b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_memory",
        sa.Column(
            "current_filter",
            JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "user_memory",
        sa.Column(
            "consultation_status",
            JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_memory", "consultation_status")
    op.drop_column("user_memory", "current_filter")
