"""add attributes_table_text and variants_table_text column into laptops table

Revision ID: a82df6864590
Revises: 3e599afc79dd
Create Date: 2025-06-02 14:52:38.508585

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a82df6864590"
down_revision: Union[str, None] = "3e599afc79dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "laptops",
        sa.Column("attributes_table_text", sa.Text(), nullable=True, default=None),
    )
    op.add_column(
        "laptops",
        sa.Column("variants_table_text", sa.Text(), nullable=True, default=None),
    )


def downgrade() -> None:
    op.drop_column("laptops", "variants_table_text")
    op.drop_column("laptops", "attributes_table_text")
