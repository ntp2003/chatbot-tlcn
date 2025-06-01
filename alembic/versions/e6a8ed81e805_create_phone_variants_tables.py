"""create phone_variants tables

Revision ID: e6a8ed81e805
Revises: 3fbbfde3227e
Create Date: 2025-05-28 14:54:53.547689

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR


# revision identifiers, used by Alembic.
revision: str = "e6a8ed81e805"
down_revision: Union[str, None] = "3fbbfde3227e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    op.execute(
        """
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 
        FROM pg_catalog.pg_ts_config 
        WHERE cfgname = 'vietnamese_simple_unaccent'
      ) THEN
        CREATE TEXT SEARCH CONFIGURATION vietnamese_simple_unaccent (COPY = simple);
        ALTER TEXT SEARCH CONFIGURATION vietnamese_simple_unaccent
          ALTER MAPPING FOR hword, hword_part, word
          WITH unaccent, simple;
      END IF;
    END
    $$;
    """
    )

    op.create_table(
        "phone_variants",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("phone_id", sa.Text, nullable=False),
        sa.Column("data", JSONB, nullable=False, default={}),
        sa.Column("attributes", sa.ARRAY(JSONB), nullable=False, default={}),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("sku", sa.Text, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("variants", sa.ARRAY(JSONB), nullable=False, default=[]),
        sa.Column("color_tsv", TSVECTOR, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["phone_id"], ["phones.id"], ondelete="CASCADE"),
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION phone_variants_color_tsv_trigger()
    RETURNS trigger AS $$
    DECLARE
      color_list TEXT;
    BEGIN
      /*
       * Chúng ta sẽ trích xuất tất cả phần tử JSONB trong mảng NEW.variants
       * với điều kiện elem->>'propertyName' = 'color', rồi nối các giá trị 'value'
       * (hoặc 'displayValue') thành một chuỗi, ví dụ: 'Trắng Xanh Đỏ'.
       *
       * công thức JSONB:
       *   jsonb_array_elements(NEW.variants) trả về setof JSONB (từng phần tử trong mảng).
       *   elem->>'propertyName' = 'color' để lọc ra phần tử màu.
       *   elem->>'value' để lấy màu thực sự. Nếu bạn muốn ưu tiên 'displayValue', thay 'value' bằng 'displayValue'.
       *
       * Sau khi có chuỗi màu, chúng ta gọi to_tsvector('vietnamese_simple_unaccent', color_list).
       */

      SELECT string_agg(elem->>'value', ' ')
      INTO color_list
      FROM unnest(NEW.variants) AS elem
      WHERE elem->>'propertyName' = 'color';

      IF color_list IS NULL THEN
        color_list := '';
      END IF;

      NEW.color_tsv := to_tsvector('vietnamese_simple_unaccent', color_list);
      RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
    CREATE TRIGGER trg_phone_variants_color_tsv
    BEFORE INSERT OR UPDATE ON phone_variants
    FOR EACH ROW
    EXECUTE PROCEDURE phone_variants_color_tsv_trigger();
    """
    )

    op.execute(
        """
    UPDATE phone_variants
    SET color_tsv = (
      SELECT to_tsvector('vietnamese_simple_unaccent',
        COALESCE(string_agg(elem->>'value', ' '), '')
      )
      FROM unnest(variants) AS elem
      WHERE elem->>'propertyName' = 'color'
    );
    """
    )

    op.create_index(
        "ix_phone_variants_color_tsv_gin",
        "phone_variants",
        ["color_tsv"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_table("phone_variants")
    op.execute("DROP FUNCTION IF EXISTS phone_variants_color_tsv_trigger();")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS vietnamese_simple_unaccent;")
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
