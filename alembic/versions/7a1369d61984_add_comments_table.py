"""add comments table

Revision ID: 7a1369d61984
Revises: c138b9792231
Create Date: 2025-06-09 16:42:34.326813

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a1369d61984"
down_revision: Union[str, None] = "c138b9792231"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.BigInteger(), nullable=False, primary_key=True),
        sa.Column("product_id", sa.String(50), nullable=False, index=True),
        sa.Column("product_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "creation_time", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("creation_time_display", sa.String(50), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=False, default=0),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_administrator", sa.Boolean(), nullable=False, default=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String(100)), nullable=False, default=list),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("comments")
