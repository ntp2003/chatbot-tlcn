"""create_laptop

Revision ID: 8a431df92395
Revises: 535089ddf724
Create Date: 2025-04-06 13:17:04.906310

"""

# alembic revision -m "create_laptop"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB,ARRAY,JSON
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '8a431df92395'
down_revision: Union[str, None] = '535089ddf724'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # create table laptops
    op.create_table(
        'laptops',
        sa.Column('id', sa.Text, primary_key=True),
        sa.Column('data', JSONB, nullable=False,default={}),
        sa.Column('name',sa.Text, nullable=False),
        sa.Column('slug', sa.Text, nullable=False),
        sa.Column('brand_code', sa.Text, nullable=False),
        sa.Column('product_type', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('promotions', sa.ARRAY(sa.JSON), nullable=False),
        sa.Column('skus', sa.ARRAY(sa.JSON), nullable=False),
        #sa.Column('key_selling_points', ARRAY(JSON), nullable=False),
        sa.Column('key_selling_points', sa.ARRAY(sa.JSON), nullable=False),
        sa.Column('price', sa.BigInteger, nullable=False),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('name_embedding', Vector, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.utcnow() #server_default=sa.text('CURRENT_TIMESTAMP'),

        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            default=sa.func.utcnow(),
            onupdate=sa.func.utcnow()
        )
    )
    # indexes
    '''
    op.create_index('idx_laptops_name', 'laptops', ['name'])
    op.create_index('idx_laptops_brand_code', 'laptops', ['brand_code'])
    op.create_index('idx_laptops_product_type', 'laptops', ['product_type'])
    '''
    # foreign key laptops.brand_code -> brands.id
    op.create_foreign_key(
        'fk_laptops_brand',
        'laptops',
        'brands',
        ['brand_code'],
        ['id'],
        ondelete='CASCADE'
    
    )


def downgrade():
    # Xóa foreign key
    op.drop_constraint('fk_laptops_brand', 'laptops',type_="foreignkey")
    
    # Xóa các index
    '''
    op.drop_index('idx_laptops_name')
    op.drop_index('idx_laptops_brand_code')
    op.drop_index('idx_laptops_product_type')
    '''
    # Xóa bảng laptops
    op.drop_table('laptops')
