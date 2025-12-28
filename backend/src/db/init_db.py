"""
Script d'initialisation de la base de données.

Crée toutes les tables définies dans les modèles.
À exécuter une fois au démarrage ou utiliser Alembic pour les migrations.
"""

from src.db.base import Base
from src.db.session import engine
from src.users.models import User
from src.reservations.models import Reservation


def init_db():
    """Crée toutes les tables"""
    print("Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès!")


if __name__ == "__main__":
    init_db()
