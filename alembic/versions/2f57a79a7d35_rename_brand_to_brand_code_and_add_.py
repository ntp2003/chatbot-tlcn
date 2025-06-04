"""rename brand to brand_code and add brand_name to user_memory

Revision ID: 2f57a79a7d35
Revises: df9b9ff692d4
Create Date: 2025-04-18 22:43:51.205994

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f57a79a7d35"
down_revision: Union[str, None] = "df9b9ff692d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("user_memory", "brand", new_column_name="brand_code")

    op.add_column("user_memory", sa.Column("brand_name", sa.Text, nullable=True))


def downgrade() -> None:
    op.alter_column("user_memory", "brand_code", new_column_name="brand")
    op.drop_column("user_memory", "brand_name")
