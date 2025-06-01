"""add attributes_table_text and variants_table_text column into phones table

Revision ID: 7cdbdf78c95f
Revises: ecf72d31b89c
Create Date: 2025-06-01 08:18:06.753416

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7cdbdf78c95f"
down_revision: Union[str, None] = "ecf72d31b89c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "phones",
        sa.Column("attributes_table_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "phones",
        sa.Column("variants_table_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("phones", "variants_table_text")
    op.drop_column("phones", "attributes_table_text")
