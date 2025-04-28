"""add_gender_to__usermemory_table

Revision ID: d386e4ad157d
Revises: 51eafed45404
Create Date: 2025-04-26 03:28:12.432571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd386e4ad157d'
down_revision: Union[str, None] = '51eafed45404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add gender column with default value 'unknown'
    op.add_column('user_memory', sa.Column('gender', sa.String(50), nullable=False, default='unknown'))


def downgrade() -> None:
    # Remove gender column
    op.drop_column('user_memory', 'gender') 
