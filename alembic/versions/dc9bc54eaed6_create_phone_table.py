"""create phone table

Revision ID: dc9bc54eaed6
Revises: 120a604fd902
Create Date: 2024-10-06 21:48:50.464839

"""

# second version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "dc9bc54eaed6"
down_revision: Union[str, None] = "120a604fd902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "phones",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("data", JSONB, nullable=False, default={}),
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
    op.drop_table("phones")
