from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, time


class UserUpdateRequest(BaseModel):
    """Mise à jour des informations utilisateur"""
    prenom: Optional[str] = None
    nom: Optional[str] = None
    phone: Optional[str] = None


class ReservationData(BaseModel):
    """Données de réservation avec choix de menu"""
    date_reservation: str  # Format: YYYY-MM-DD
    heure_reservation: str  # Format: HH:MM
    habite_residence: bool
    numero_chambre: Optional[str] = None
    numero_immeuble: Optional[str] = None
    adresse: Optional[str] = None
    phone: str
    menu_id: Optional[str] = None
    boisson_id: Optional[str] = None
    bonus_ids: Optional[List[str]] = None  # Liste d'IDs d'extras
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Valider le numéro de téléphone"""
        if not v or len(v) < 10:
            raise ValueError("Le numéro de téléphone doit contenir au moins 10 caractères")
        return v


class MenuItemResponse(BaseModel):
    """Réponse pour un MenuItem"""
    id: int
    name: str
    price: float
    item_type: str
    
    class Config:
        from_attributes = True


class UserWithReservationResponse(BaseModel):
    """Réponse utilisateur avec détails de réservation"""
    id: int
    email: str
    prenom: Optional[str]
    nom: Optional[str]
    email_verified: bool
    is_cotisant: bool
    
    # Détails réservation
    date_reservation: Optional[str]
    heure_reservation: Optional[str]
    habite_residence: Optional[bool]
    adresse: Optional[str]
    phone: Optional[str]
    
    # Items de menu
    menu_item: Optional[MenuItemResponse]
    boisson_item: Optional[MenuItemResponse]
    extras_items: Optional[List[MenuItemResponse]] = None  # Liste d'extras
    
    # Paiement
    payment_status: str
    total_amount: float
    
    class Config:
        from_attributes = True
