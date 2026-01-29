"""change menu fields to foreign keys

Revision ID: 001
Revises: 
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Supprimer les anciennes colonnes String
    # op.drop_column('users', 'menu')
    # op.drop_column('users', 'boisson')
    # op.drop_column('users', 'bonus')
    
    # Ajouter les nouvelles colonnes ForeignKey
    op.add_column('users', sa.Column('menu_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('boisson_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('bonus_id', sa.Integer(), nullable=True))
    
    # Créer les Foreign Keys
    op.create_foreign_key(
        'fk_users_menu_id_menu_items',
        'users', 'menu_items',
        ['menu_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_boisson_id_menu_items',
        'users', 'menu_items',
        ['boisson_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_bonus_id_menu_items',
        'users', 'menu_items',
        ['bonus_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Supprimer les Foreign Keys
    op.drop_constraint('fk_users_bonus_id_menu_items', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_boisson_id_menu_items', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_menu_id_menu_items', 'users', type_='foreignkey')
    
    # Supprimer les colonnes ForeignKey
    op.drop_column('users', 'bonus_id')
    op.drop_column('users', 'boisson_id')
    op.drop_column('users', 'menu_id')
    
    # Remettre les colonnes String
    op.add_column('users', sa.Column('menu', sa.String(), nullable=True))
    op.add_column('users', sa.Column('boisson', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bonus', sa.String(), nullable=True))
