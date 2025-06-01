"""add color and rom column into user_memory table

Revision ID: ecf72d31b89c
Revises: e6a8ed81e805
Create Date: 2025-05-31 10:33:14.486457

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "ecf72d31b89c"
down_revision: Union[str, None] = "e6a8ed81e805"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_memory",
        sa.Column("color", sa.String(), nullable=True),
    )
    op.add_column(
        "user_memory",
        sa.Column("rom", JSONB, nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("user_memory", "rom")
    op.drop_column("user_memory", "color")
