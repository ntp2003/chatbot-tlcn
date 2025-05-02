"""create_laptop_table

Revision ID: 91ff766d4eb5
Revises: 0608f442d05b
Create Date: 2025-04-29 10:54:17.483922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '91ff766d4eb5'
down_revision: Union[str, None] = '0608f442d05b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create laptops table
    op.create_table(
        'laptops',
        sa.Column('id', sa.Text, primary_key=True),
        sa.Column('data', JSONB, nullable=False, default={}),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('slug', sa.Text, nullable=False),
        sa.Column('brand_code', sa.Text, nullable=False),
        sa.Column('product_type', sa.Text, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('promotions', sa.ARRAY(sa.JSON()), nullable=False),
        sa.Column('skus', sa.ARRAY(sa.JSON()), nullable=False),
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
        #sa.PrimaryKeyConstraint('id')
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_laptops_brand_code_brands',
        'laptops', 'brands',
        ['brand_code'], ['id'],
        ondelete='CASCADE'
    )

    # Add indexes
    '''
    op.create_index('idx_laptops_brand_code', 'laptops', ['brand_code'])
    op.create_index('idx_laptops_name', 'laptops', ['name'])
    op.create_index('idx_laptops_price', 'laptops', ['price'])
    '''


def downgrade() -> None:
    # Drop indexes
    '''
    op.drop_index('idx_laptops_price')
    op.drop_index('idx_laptops_name')
    op.drop_index('idx_laptops_brand_code')
    '''
    # Drop foreign key
    op.drop_constraint('fk_laptops_brand_code_brands', 'laptops', type_='foreignkey')
    
    # Drop table
    op.drop_table('laptops')
