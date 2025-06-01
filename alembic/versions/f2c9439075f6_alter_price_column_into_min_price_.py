"""alter price column into min_price column and add max_price column of phones_table

Revision ID: f2c9439075f6
Revises: 7cdbdf78c95f
Create Date: 2025-06-01 09:00:49.489978

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2c9439075f6"
down_revision: Union[str, None] = "7cdbdf78c95f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "phones",
        "price",
        new_column_name="min_price",
        existing_type=sa.Integer,
        nullable=False,
    )
    op.add_column(
        "phones",
        sa.Column("max_price", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("phones", "max_price")
    op.alter_column(
        "phones",
        "min_price",
        new_column_name="price",
        existing_type=sa.Integer,
        nullable=False,
    )
