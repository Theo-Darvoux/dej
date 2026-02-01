"""change bonus_ids to jsonb

Revision ID: 007
Revises: 006_add_email_delivery_status
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert bonus_ids column from json to jsonb
    # PostgreSQL can cast json to jsonb directly
    op.execute("ALTER TABLE users ALTER COLUMN bonus_ids TYPE jsonb USING bonus_ids::jsonb")


def downgrade() -> None:
    # Convert bonus_ids column from jsonb back to json
    op.execute("ALTER TABLE users ALTER COLUMN bonus_ids TYPE json USING bonus_ids::json")
