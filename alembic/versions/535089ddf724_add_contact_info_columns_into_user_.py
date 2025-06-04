"""add contact info columns into user memory table

Revision ID: 535089ddf724
Revises: 0113278eac18
Create Date: 2024-11-30 21:30:52.914493

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "535089ddf724"
down_revision: Union[str, None] = "0113278eac18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_memory",
        sa.Column("phone_number", sa.Text, nullable=True),
    )
    op.add_column(
        "user_memory",
        sa.Column("email", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_memory", "phone_number")
    op.drop_column("user_memory", "email")
