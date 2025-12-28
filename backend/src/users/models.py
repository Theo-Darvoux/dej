from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.db.base import Base
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    prenom = Column(String, nullable=True)
    nom = Column(String, nullable=True)
    
    # Vérification email
    email_verified = Column(Boolean, default=False, index=True)
    verification_code = Column(String, nullable=True)  # Code à 4 chiffres
    code_created_at = Column(DateTime, nullable=True)  # Timestamp création du code
    
    # BDE vérification
    is_cotisant = Column(Boolean, default=False)  # Vérifié via BDE API
    cotisant_checked_at = Column(DateTime, nullable=True)  # Dernière vérif BDE
    
    # Paiement
    payment_status = Column(String, default="pending")  # pending, completed, failed
    payment_date = Column(DateTime, nullable=True)
    
    # Métadonnées
    user_type = Column(String, nullable=True)  # None (normal), "Listeux", "admin"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relations
    reservations = relationship("Reservation", back_populates="user")

