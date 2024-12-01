"""modify name_embedding column of phones table to not nullable

Revision ID: 0113278eac18
Revises: 71321ac3cff1
Create Date: 2024-11-27 20:51:01.834963

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0113278eac18"
down_revision: Union[str, None] = "71321ac3cff1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "phones",
        "name_embedding",
        existing_type=Vector,
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "phones",
        "name_embedding",
        existing_type=Vector,
        nullable=True,
    )
