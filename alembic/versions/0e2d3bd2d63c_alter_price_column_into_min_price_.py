"""alter price column into min_price column and add max_price column of phones_table

Revision ID: 0e2d3bd2d63c
Revises: a82df6864590
Create Date: 2025-06-02 14:55:31.882709

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0e2d3bd2d63c"
down_revision: Union[str, None] = "a82df6864590"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "laptops",
        "price",
        new_column_name="min_price",
        existing_type=sa.Integer,
        nullable=False,
    )
    op.add_column(
        "laptops",
        sa.Column("max_price", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("laptops", "max_price")
    op.alter_column(
        "laptops",
        "min_price",
        new_column_name="price",
        existing_type=sa.Integer,
        nullable=False,
    )
