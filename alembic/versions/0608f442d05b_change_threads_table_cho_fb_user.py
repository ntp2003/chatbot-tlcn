"""change threads table cho fb user

Revision ID: 0608f442d05b
Revises: 82a673d9cba9
Create Date: 2025-04-27 17:55:30.751210

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0608f442d05b"
down_revision: Union[str, None] = "82a673d9cba9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "threads",
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )


def downgrade() -> None:
    op.drop_column("threads", "is_active")
