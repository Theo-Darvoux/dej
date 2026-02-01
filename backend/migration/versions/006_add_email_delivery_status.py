"""add email_delivery_status column

Revision ID: 006
Revises: 005_change_menu_ids_to_string
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005_change_menu_ids_to_string'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email_delivery_status column with default value
    op.add_column('users', sa.Column('email_delivery_status', sa.String(), nullable=True, server_default='pending'))
    
    # Update existing rows to have 'pending' value
    op.execute("UPDATE users SET email_delivery_status = 'pending' WHERE email_delivery_status IS NULL")
    

def downgrade() -> None:
    # Remove email_delivery_status column
    op.drop_column('users', 'email_delivery_status')
