from pydantic import BaseModel
from typing import List, Optional


class TerminalOrder(BaseModel):
    """Order card for terminal kitchen display"""
    id: int
    prenom: Optional[str]
    nom: Optional[str]
    is_maisel: bool  # True = Maisel residence, False = Evry
    batiment: Optional[str]  # U1-U7 if Maisel
    chambre: Optional[int]  # Room number if Maisel
    menu: Optional[str]
    boisson: Optional[str]
    extras: List[str] = []
    heure: str  # Format HH:MM

    class Config:
        from_attributes = True


class TerminalOrdersResponse(BaseModel):
    """Response for terminal orders"""
    orders: List[TerminalOrder]
    current_hour: int
    total: int
