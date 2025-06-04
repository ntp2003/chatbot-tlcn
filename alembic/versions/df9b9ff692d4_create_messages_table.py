"""create messages table

Revision ID: df9b9ff692d4
Revises: 888cecf62e00
Create Date: 2025-04-11 23:52:35.081614

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM

# Tạo enum type
message_type_enum = sa.Enum("user", "bot", name="message_type_enum")

# revision identifiers, used by Alembic.
revision: str = "df9b9ff692d4"
down_revision: Union[str, None] = "888cecf62e00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "messages",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "thread_id",
            UUID(as_uuid=True),
            sa.ForeignKey("threads.id"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", message_type_enum, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
            onupdate=sa.func.utcnow(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            default=sa.func.utcnow(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("messages")
    message_type_enum.drop(op.get_bind(), checkfirst=True)
