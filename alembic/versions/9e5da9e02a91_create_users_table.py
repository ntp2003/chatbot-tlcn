"""Create users table

Revision ID: 9e5da9e02a91
Revises: dc9bc54eaed6
Create Date: 2024-10-12 14:57:32.616655

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = "9e5da9e02a91"
down_revision: Union[str, None] = "dc9bc54eaed6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        ),
        sa.Column("user_name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("password", sa.String(length=50), nullable=False),
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
        sa.UniqueConstraint("user_name", name="uq_users_user_name"),
    )


def downgrade() -> None:
    op.drop_table("users")
