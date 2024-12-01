"""add embedding column for phone name into phones table

Revision ID: 71321ac3cff1
Revises: 45d35c46a219
Create Date: 2024-11-27 20:44:27.043337

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "71321ac3cff1"
down_revision: Union[str, None] = "45d35c46a219"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "phones",
        sa.Column("name_embedding", Vector, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("phones", "name_embedding")
