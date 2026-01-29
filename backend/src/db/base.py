from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models so Alembic autogenerate can discover all tables
# These imports are placed AFTER Base definition to avoid circular imports
def import_models():
    """Import all models for Alembic autogenerate discovery."""
    from src.users.models import User  # noqa: F401
    from src.reservations.models import MenuItemLimit  # noqa: F401
