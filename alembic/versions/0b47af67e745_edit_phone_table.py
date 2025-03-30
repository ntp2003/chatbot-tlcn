"""Edit Phone table

Revision ID: 0b47af67e745
Revises: 672acb86aec9
Create Date: 2024-11-19 23:21:08.599080

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0b47af67e745"
down_revision: Union[str, None] = "672acb86aec9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("phones", sa.Column("name", sa.Text, nullable=True))
    op.add_column("phones", sa.Column("slug", sa.Text, nullable=True))
    op.add_column("phones", sa.Column("brand_code", sa.Text, nullable=True))
    op.add_column("phones", sa.Column("product_type", sa.Text, nullable=True))
    op.add_column("phones", sa.Column("description", sa.Text, nullable=True))
    op.add_column(
        "phones",
        sa.Column("promotions", sa.ARRAY(sa.JSON), nullable=True),
    )
    op.add_column(
        "phones",
        sa.Column("skus", sa.ARRAY(sa.JSON), nullable=True),
    )
    op.add_column(
        "phones",
        sa.Column("key_selling_points", sa.ARRAY(sa.JSON), nullable=True),
    )
    op.add_column(
        "phones",
        sa.Column("price", sa.BigInteger, nullable=True),
    )
    op.add_column(
        "phones",
        sa.Column("score", sa.Float, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("phones", "name")
    op.drop_column("phones", "brand_code")
    op.drop_column("phones", "slug")
    op.drop_column("phones", "product_type")
    op.drop_column("phones", "description")
    op.drop_column("phones", "promotions")
    op.drop_column("phones", "skus")
    op.drop_column("phones", "key_selling_points")
    op.drop_column("phones", "price")
    op.drop_column("phones", "score")
