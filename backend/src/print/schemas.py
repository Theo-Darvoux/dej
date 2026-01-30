from pydantic import BaseModel
from typing import List, Optional

class OrderCombo(BaseModel):
    menu: Optional[str]
    boisson: Optional[str]
    extras: List[str] = []
    quantity: int

class PrintSummaryResponse(BaseModel):
    start_time: str
    end_time: str
    combos: List[OrderCombo]
    total_orders: int


class OrderItem(BaseModel):
    """Individual order for list view"""
    id: int
    prenom: Optional[str]
    nom: Optional[str]
    heure_reservation: str
    menu: Optional[str]
    boisson: Optional[str]
    extras: List[str] = []
    payment_status: str
    is_maisel: bool  # True if Maisel residence, False if Evry
    adresse: Optional[str]

    class Config:
        from_attributes = True


class OrdersListResponse(BaseModel):
    """Paginated orders list response"""
    orders: List[OrderItem]
    total: int
    page: int
    per_page: int
    total_pages: int
