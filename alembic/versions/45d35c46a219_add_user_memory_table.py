"""Add user_memory table

Revision ID: 45d35c46a219
Revises: 806ac93114b7
Create Date: 2024-11-23 22:11:59.737540

"""
# ninth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "45d35c46a219"
down_revision: Union[str, None] = "806ac93114b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
from sqlalchemy.dialects.postgresql import UUID


def upgrade() -> None:
    op.create_table(
        "user_memory",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_demand", sa.Text, nullable=True),
        sa.Column("product_name", sa.Text, nullable=True),
        sa.Column("brand", sa.Text, nullable=True),
        sa.Column("min_price", sa.Integer, nullable=True),
        sa.Column("max_price", sa.Float, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("user_memory")
