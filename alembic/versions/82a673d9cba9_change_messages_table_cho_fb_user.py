"""change messages table cho fb user

Revision ID: 82a673d9cba9
Revises: 9591ad7cc8d3
Create Date: 2025-04-27 17:31:58.244760

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "82a673d9cba9"
down_revision: Union[str, None] = "9591ad7cc8d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("fb_message_id", sa.String(100), nullable=True))
    op.execute("ALTER TYPE message_type_enum ADD VALUE 'page_admin'")


def downgrade() -> None:
    op.drop_column("messages", "fb_message_id")
    op.execute("CREATE TYPE message_type_enum_new AS ENUM ('user', 'bot')")
    op.execute("UPDATE messages SET type = 'bot' WHERE type = 'page_admin'")
    op.execute(
        "ALTER TABLE messages ALTER COLUMN type TYPE message_type_enum_new USING type::text::message_type_enum_new"
    )
    op.execute("DROP TYPE message_type_enum")
    op.execute("ALTER TYPE message_type_enum_new RENAME TO message_type_enum")
