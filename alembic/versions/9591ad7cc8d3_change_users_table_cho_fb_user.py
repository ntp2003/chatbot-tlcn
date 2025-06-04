"""change users table cho fb user

Revision ID: 9591ad7cc8d3
Revises: ee9837b95476
Create Date: 2025-04-27 17:26:39.123607

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9591ad7cc8d3"
down_revision: Union[str, None] = "ee9837b95476"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = sa.Enum("admin", "chainlit_user", "fb_user", name="userrole")


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="chainlit_user",
        ),
    )
    op.alter_column(
        "users", "password", existing_type=sa.String(length=50), nullable=True
    )
    op.add_column(
        "users",
        sa.Column("fb_user_id", sa.String(50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("gender", sa.String(10), nullable=True),
    )
    op.drop_constraint("uq_users_user_name", "users")


def downgrade() -> None:
    op.drop_column("users", "role")
    op.execute("UPDATE users SET password = 'NULL' WHERE password IS NULL")
    op.alter_column(
        "users", "password", existing_type=sa.String(length=50), nullable=False
    )
    op.drop_column("users", "fb_user_id")
    op.drop_column("users", "gender")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
    op.create_unique_constraint(
        "uq_users_user_name", "users", ["user_name"], schema=None
    )
