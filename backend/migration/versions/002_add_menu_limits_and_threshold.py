"""add menu limits and threshold

Revision ID: 002
Revises: 001
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create MenuItemLimit table
    op.create_table(
        'menu_item_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('menu_item_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('max_quantity', sa.Integer(), nullable=True),
        sa.Column('current_quantity', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_item_limits_id'), 'menu_item_limits', ['id'], unique=False)
    op.create_index(op.f('ix_menu_item_limits_menu_item_id'), 'menu_item_limits', ['menu_item_id'], unique=False)

    # 2. Add low_stock_threshold to menu_items
    op.add_column('menu_items', sa.Column('low_stock_threshold', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('menu_items', 'low_stock_threshold')
    op.drop_index(op.f('ix_menu_item_limits_menu_item_id'), table_name='menu_item_limits')
    op.drop_index(op.f('ix_menu_item_limits_id'), table_name='menu_item_limits')
    op.drop_table('menu_item_limits')
