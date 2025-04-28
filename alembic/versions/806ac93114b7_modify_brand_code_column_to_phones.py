"""modify  brand_code column to phones

Revision ID: 806ac93114b7
Revises: f4873b4eba7e
Create Date: 2024-11-23 17:48:33.700185

"""
# eighth version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "806ac93114b7"
down_revision: Union[str, None] = "f4873b4eba7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_phones_brand_code",
        "phones",
        "brands",
        ["brand_code"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_phones_brand_code", "phones", type_="foreignkey")
