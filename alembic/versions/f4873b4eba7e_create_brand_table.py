"""create brands table

Revision ID: f4873b4eba7e
Revises: dd89958929b9
Create Date: 2024-11-23 17:26:58.534216

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "f4873b4eba7e"
down_revision: Union[str, None] = "dd89958929b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("embedding", Vector, nullable=False),
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
    op.drop_table("brands")
