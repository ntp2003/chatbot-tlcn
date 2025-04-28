"""set contraint not null to phone table

Revision ID: dd89958929b9
Revises: 0b47af67e745
Create Date: 2024-11-23 09:27:34.079096

"""

# sixth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dd89958929b9"
down_revision: Union[str, None] = "0b47af67e745"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "phones",
        "slug",
        existing_type=sa.Text,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "name",
        existing_type=sa.Text,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "brand_code",
        existing_type=sa.Text,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "product_type",
        existing_type=sa.Text,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "description",
        existing_type=sa.Text,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "promotions",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=False,
    )
    op.alter_column(
        "phones",
        "skus",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=False,
    )
    op.alter_column(
        "phones",
        "key_selling_points",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=False,
    )
    op.alter_column(
        "phones",
        "price",
        existing_type=sa.BigInteger,
        nullable=False,
    )
    op.alter_column(
        "phones",
        "score",
        existing_type=sa.Float,
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "phones",
        "slug",
        existing_type=sa.Text,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "name",
        existing_type=sa.Text,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "brand_code",
        existing_type=sa.Text,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "product_type",
        existing_type=sa.Text,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "description",
        existing_type=sa.Text,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "promotions",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=True,
    )
    op.alter_column(
        "phones",
        "skus",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=True,
    )
    op.alter_column(
        "phones",
        "key_selling_points",
        existing_type=sa.ARRAY(sa.JSON),
        nullable=True,
    )
    op.alter_column(
        "phones",
        "price",
        existing_type=sa.BigInteger,
        nullable=True,
    )
    op.alter_column(
        "phones",
        "score",
        existing_type=sa.Float,
        nullable=True,
    )
