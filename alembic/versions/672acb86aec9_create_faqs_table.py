"""Create faqs table

Revision ID: 672acb86aec9
Revises: 9e5da9e02a91
Create Date: 2024-10-14 13:37:59.230856

"""

# fourth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

# revision identifiers, used by Alembic.
revision: str = "672acb86aec9"
down_revision: Union[str, None] = "9e5da9e02a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "faqs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("embedding", VECTOR, nullable=False),
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
    op.drop_table("faqs")
