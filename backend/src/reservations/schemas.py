from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum



class BatimentMaisel(str, Enum):
    U1 = "U1"
    U2 = "U2"
    U3 = "U3"
    U4 = "U4"
    U5 = "U5"
    U6 = "U6"
    U7 = "U7"

class ReservationCreateRequest(BaseModel):
    """Création d'une réservation"""
    date_reservation: str  # Format: YYYY-MM-DD
    heure_reservation: str  # Format: HH:MM
    habite_residence: bool
    numero_chambre: Optional[str] = None  # Si habite_residence=True
    numero_immeuble: Optional[str] = None  # Si habite_residence=True
    adresse: Optional[str] = None  # Si habite_residence=False



class ReservationResponse(BaseModel):
    """Réponse réservation"""
    id: int
    user_id: int
    date_reservation: str
    heure_reservation: str
    habite_residence: bool
    numero_chambre: Optional[str]
    numero_immeuble: Optional[str]
    adresse: Optional[str]
    payment_status: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentIntentRequest(BaseModel):
    """Demande création intent HelloAsso"""
    reservation_id: int


class PaymentIntentResponse(BaseModel):
    """Réponse intent HelloAsso"""
    intent_id: str
    redirect_url: str  # URL HelloAsso pour paiement


class PaymentConfirmResponse(BaseModel):
    """Confirmation paiement"""
    message: str
    reservation_id: int
    payment_status: str
