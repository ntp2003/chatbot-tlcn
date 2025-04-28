"""add intent column to user_memory

Revision ID: b0b9ba1f513b
Revises: 2f57a79a7d35
Create Date: 2025-04-19 13:09:03.938704

"""
# sixteenth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b0b9ba1f513b"
down_revision: Union[str, None] = "2f57a79a7d35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_memory",
        sa.Column(
            "intent",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_memory", "intent")
