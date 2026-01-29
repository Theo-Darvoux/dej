from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime, ForeignKey, Time, Enum as SAEnum, Float
from sqlalchemy.orm import relationship
from src.db.base import Base
from datetime import datetime, timezone
from src.reservations.schemas import BatimentMaisel

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    normalized_email = Column(String, unique=True, nullable=False, index=True)
    prenom = Column(String, nullable=True)
    nom = Column(String, nullable=True)
    
    # Vérification email
    email_verified = Column(Boolean, default=False, index=True)
    verification_code = Column(String, nullable=True)  # Code à 4 chiffres
    code_created_at = Column(DateTime, nullable=True)  # Timestamp création du code
    
    # BDE vérification
    is_cotisant = Column(Boolean, default=False)  # Vérifié via BDE API
    cotisant_checked_at = Column(DateTime, nullable=True)  # Dernière vérif BDE
    
    # Détails réservation
    date_reservation = Column(Date, nullable=True)
    heure_reservation = Column(Time, nullable=True)
    
    # Logement
    habite_residence = Column(Boolean, nullable=True)
    adresse_if_maisel = Column(SAEnum(BatimentMaisel, name="maisel_batiment_enum"), nullable=True)
    numero_if_maisel = Column(Integer, nullable=True)
    adresse = Column(String, nullable=True)
    
    # Contact et commande
    phone = Column(String, nullable=True)
    special_requests = Column(String, nullable=True)  # Demandes spéciales client
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # Paiement
    payment_status = Column(String, default="pending")  # pending, completed, failed
    payment_intent_id = Column(String, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    payment_attempts = Column(Integer, default=0)
    reservation_expires_at = Column(DateTime, nullable=True)
    
    # Métadonnées
    last_ip = Column(String, nullable=True)
    user_type = Column(String, nullable=True)  # None (normal), "Listeux", "admin"
    status = Column(String, default="confirmed")
    status_token = Column(String, nullable=True, index=True)  # Token unique pour page statut commande
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Choix de commande - IDs from JSON (Strings)
    menu_id = Column(String, nullable=True)
    boisson_id = Column(String, nullable=True)
    bonus_id = Column(String, nullable=True)
    
    # Relations removed as we interpret IDs from JSON now

