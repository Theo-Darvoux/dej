from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime, ForeignKey, Time, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.db.base import Base
from datetime import datetime, timezone
from src.reservations.schemas import BatimentMaisel




class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Détails réservation
    date_reservation = Column(Date, nullable=False)  # Format: YYYY-MM-DD
    heure_reservation = Column(Time, nullable=False)  # Format: HH:MM
    
    # Logement
    habite_residence = Column(Boolean, nullable=False)  # True = résidence, False = autre
    
    adresse_if_maisel = Column(SAEnum(BatimentMaisel, name="maisel_batiment_enum"), nullable=True)  # U1..U7 uniquement
    numero_if_maisel = Column(Integer, nullable=True)  # Si habite_residence=True
    adresse = Column(String, nullable=True)  # Si habite_residence=False
    
    # Paiement
    payment_status = Column(String, default="pending")  # pending, completed, failed
    payment_intent_id = Column(String, nullable=True)  # HelloAsso intent ID
    payment_date = Column(DateTime, nullable=True)
    
    # Métadonnées
    status = Column(String, default="confirmed")  # confirmed, cancelled, completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relation
    user = relationship("User", back_populates="reservations")