from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime, ForeignKey, Time, Enum as SAEnum, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
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
    
    # Contact et commande
    phone = Column(String, nullable=True)  # Numéro de téléphone pour livraison
    total_amount = Column(Float, nullable=False, default=0.0)  # Montant total en euros
    
    # Paiement
    payment_status = Column(String, default="pending")  # pending, completed, failed
    payment_intent_id = Column(String, nullable=True)  # HelloAsso intent ID
    payment_date = Column(DateTime, nullable=True)
    
    # Métadonnées
    status = Column(String, default="confirmed")  # confirmed, cancelled, completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relations
    user = relationship("User", back_populates="reservations")
    items = relationship("ReservationItem", back_populates="reservation")


class ReservationItem(Base):
    __tablename__ = "reservation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # Prix au moment de la commande
    
    # Relations
    reservation = relationship("Reservation", back_populates="items")
    menu_item = relationship("MenuItem")