"""add checkout_redirect_url and checkout_created_at fields

Revision ID: 008
Revises: 007
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns for checkout reuse functionality
    op.add_column('users', sa.Column('checkout_redirect_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('checkout_created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'checkout_created_at')
    op.drop_column('users', 'checkout_redirect_url')
