from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.config import settings

# Créer l'engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # À passer à True pour debug SQL
    future=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db() -> Session:
    """Dépendance FastAPI pour injecter une session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
