"""create phone_variants tables

Revision ID: e6a8ed81e805
Revises: 3fbbfde3227e
Create Date: 2025-05-28 14:54:53.547689

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "e6a8ed81e805"
down_revision: Union[str, None] = "3fbbfde3227e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "phone_variants",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("phone_id", sa.Integer, nullable=False),
        sa.Column("data", JSONB, nullable=False, default={}),
        sa.Column("attributes", sa.ARRAY(JSONB), nullable=False, default={}),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("sku", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("variants", sa.ARRAY(JSONB), nullable=False, default=[]),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["phone_id"], ["phones.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("phone_variants")
