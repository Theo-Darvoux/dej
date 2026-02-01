"""Remove low_stock_threshold from menu_items

Revision ID: 004_remove_stock_fields
Revises: 467833cc429e
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_remove_stock_fields'
down_revision = '467833cc429e'
branch_labels = None
depends_on = None


def upgrade():
    """Remove low_stock_threshold column from menu_items table."""
    # Drop the low_stock_threshold column if it exists
    with op.batch_alter_table('menu_items', schema=None) as batch_op:
        batch_op.drop_column('low_stock_threshold')


def downgrade():
    """Re-add low_stock_threshold column to menu_items table."""
    # Add the column back
    op.add_column('menu_items', sa.Column('low_stock_threshold', sa.Integer(), nullable=True))
