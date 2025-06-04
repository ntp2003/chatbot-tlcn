"""create threads table

Revision ID: 888cecf62e00
Revises: 535089ddf724
Create Date: 2025-04-11 23:47:10.446145

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "888cecf62e00"
down_revision: Union[str, None] = "535089ddf724"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "threads",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
            onupdate=sa.func.utcnow(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("threads")
