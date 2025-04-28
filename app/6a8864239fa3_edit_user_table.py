"""edit_user_table

Revision ID: 6a8864239fa3
Revises: 8a431df92395
Create Date: 2025-04-07 09:15:48.826697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a8864239fa3'
down_revision: Union[str, None] = '8a431df92395'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # modify user_name column change type from String(50) to Text
    op.alter_column(
        'users',
        'user_name',
        type_=sa.Text(),
        existing_type=sa.String(length=50),
        existing_nullable=False,
        postgresql_using='user_name::text',
    )

    #modify password column : turn into nullable
    op.alter_column(
        'users',
        'password',
        existing_type=sa.String(length=50),
        nullable=True,
    )

    # add fb_id column
    op.add_column(
        'users',
        sa.Column('fb_id', sa.Text(), nullable=True)
    )

    # add unique constraint to fb_id column
    op.create_unique_constraint(
        'uq_users_fb_id',
        'users',
        ['fb_id']
    )
def downgrade() -> None:
    # drop unique constraint to fb_id column
    op.drop_constraint('uq_users_fb_id', 'users', type_='unique')

    # drop fb_id column
    op.drop_column('users', 'fb_id')

    #modify password column back : make it not nullable
    op.alter_column(
        'users',
        'password',
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # modify user_name column back to String(50)
    op.alter_column(
        'users',
        'user_name',
        type_=sa.String(length=50),
        existing_type=sa.Text(),
        existing_nullable=False,
        postgresql_using='user_name::varchar(50)',
    )
