from pydantic import BaseModel, field_validator
from typing import Optional
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
    menu_id: Optional[int] = None
    boisson_id: Optional[int] = None
    bonus_id: Optional[int] = None
    
    @field_validator('menu_id', 'boisson_id', 'bonus_id')
    @classmethod
    def validate_positive_ids(cls, v: Optional[int]) -> Optional[int]:
        """Valider que les IDs sont positifs s'ils sont fournis"""
        if v is not None and v <= 0:
            raise ValueError("L'ID doit être un entier positif")
        return v
    
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
    bonus_item: Optional[MenuItemResponse]
    
    # Paiement
    payment_status: str
    total_amount: float
    
    class Config:
        from_attributes = True
