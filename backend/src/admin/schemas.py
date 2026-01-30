from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from src.reservations.schemas import BatimentMaisel

class AdminOrderItem(BaseModel):
    id: str
    name: str
    price: float
    item_type: str

class AdminOrderResponse(BaseModel):
    id: int
    email: str
    prenom: Optional[str] = None
    nom: Optional[str] = None
    phone: Optional[str] = None
    payment_status: str
    status: str
    total_amount: float
    date_reservation: Optional[date] = None
    heure_reservation: Optional[time] = None
    habite_residence: Optional[bool] = None
    adresse_if_maisel: Optional[BatimentMaisel] = None
    numero_if_maisel: Optional[int] = None
    adresse: Optional[str] = None
    special_requests: Optional[str] = None
    created_at: datetime
    
    menu_item: Optional[AdminOrderItem] = None
    boisson_item: Optional[AdminOrderItem] = None
    extras_items: Optional[List[AdminOrderItem]] = []

    class Config:
        from_attributes = True

class AdminOrderUpdate(BaseModel):
    prenom: Optional[str] = None
    nom: Optional[str] = None
    phone: Optional[str] = None
    payment_status: Optional[str] = None
    date_reservation: Optional[date] = None
    heure_reservation: Optional[time] = None
    habite_residence: Optional[bool] = None
    adresse_if_maisel: Optional[BatimentMaisel] = None
    numero_if_maisel: Optional[int] = None
    adresse: Optional[str] = None
    special_requests: Optional[str] = None
    menu_id: Optional[str] = None
    boisson_id: Optional[str] = None
    bonus_ids: Optional[List[str]] = None
