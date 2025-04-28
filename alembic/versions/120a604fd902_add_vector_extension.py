"""add vector extension

Revision ID: 120a604fd902
Revises: 
Create Date: 2024-09-21 23:45:28.099326

"""

# first version
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "120a604fd902"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION vector;")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector;")
