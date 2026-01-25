"""add last_ip column

Revision ID: 003
Revises: 002
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('last_ip', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'last_ip')
