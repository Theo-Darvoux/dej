"""Change menu_id and boisson_id to String types for JSON IDs

Revision ID: 005_change_menu_ids_to_string
Revises: 004_remove_stock_fields
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_change_menu_ids_to_string'
down_revision = '004_remove_stock_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Change menu_id and boisson_id from Integer to String to store JSON IDs."""
    # Drop foreign key constraints if they exist
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_menu_id_menu_items')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_boisson_id_menu_items')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_bonus_id_menu_items')
    
    # Change column types to String
    op.alter_column('users', 'menu_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(),
                    existing_nullable=True)
    
    op.alter_column('users', 'boisson_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(),
                    existing_nullable=True)


def downgrade():
    """Revert menu_id and boisson_id back to Integer."""
    # Clear data first to avoid conversion errors
    op.execute('UPDATE users SET menu_id = NULL, boisson_id = NULL')
    
    # Change back to Integer
    op.alter_column('users', 'menu_id',
                    existing_type=sa.String(),
                    type_=sa.Integer(),
                    existing_nullable=True)
    
    op.alter_column('users', 'boisson_id',
                    existing_type=sa.String(),
                    type_=sa.Integer(),
                    existing_nullable=True)
