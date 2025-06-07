"""Add Google OAuth support

Revision ID: c138b9792231
Revises: 0e2d3bd2d63c
Create Date: 2025-06-07 06:30:50.635547

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c138b9792231"
down_revision: Union[str, None] = "0e2d3bd2d63c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Thêm 'google_user' vào enum UserRole
    op.execute("ALTER TYPE userrole ADD VALUE 'google_user'")

    # 2. Thêm các cột mới cho Google OAuth
    op.add_column("users", sa.Column("google_id", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("full_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("last_oauth_login", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("oauth_provider", sa.String(50), nullable=True))

    # 3. Tạo unique constraint cho google_id
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])

    # 4. Tạo unique constraint cho email (nếu chưa có)
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "oauth_provider")
    op.drop_column("users", "last_oauth_login")
    op.drop_column("users", "full_name")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "email")
    op.drop_column("users", "google_id")
    op.execute("ALTER TYPE userrole DROP VALUE 'google_user'")
