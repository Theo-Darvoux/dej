from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.config import settings
from typing import Generator

# Créer l'engine avec configuration du pool de connexions
# - pool_size: nombre de connexions permanentes dans le pool
# - max_overflow: connexions supplémentaires autorisées au-delà du pool_size
# - pool_recycle: durée max (secondes) avant recyclage d'une connexion
# - pool_pre_ping: vérifie la validité de la connexion avant utilisation
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # À passer à True pour debug SQL
    future=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI pour injecter une session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
