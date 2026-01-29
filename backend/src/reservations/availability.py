"""
Module de gestion des disponibilités des créneaux horaires.
"""
from sqlalchemy.orm import Session
from datetime import time
from typing import Optional

from src.reservations.models import MenuItemLimit


# Créneaux horaires disponibles (7h-8h à 19h-20h)
TIME_SLOTS = [
    {"slot": "07:00 - 08:00", "start": time(7, 0), "end": time(8, 0)},
    {"slot": "08:00 - 09:00", "start": time(8, 0), "end": time(9, 0)},
    {"slot": "09:00 - 10:00", "start": time(9, 0), "end": time(10, 0)},
    {"slot": "10:00 - 11:00", "start": time(10, 0), "end": time(11, 0)},
    {"slot": "11:00 - 12:00", "start": time(11, 0), "end": time(12, 0)},
    {"slot": "12:00 - 13:00", "start": time(12, 0), "end": time(13, 0)},
    {"slot": "13:00 - 14:00", "start": time(13, 0), "end": time(14, 0)},
    {"slot": "14:00 - 15:00", "start": time(14, 0), "end": time(15, 0)},
    {"slot": "15:00 - 16:00", "start": time(15, 0), "end": time(16, 0)},
    {"slot": "16:00 - 17:00", "start": time(16, 0), "end": time(17, 0)},
    {"slot": "17:00 - 18:00", "start": time(17, 0), "end": time(18, 0)},
    {"slot": "18:00 - 19:00", "start": time(18, 0), "end": time(19, 0)},
    {"slot": "19:00 - 20:00", "start": time(19, 0), "end": time(20, 0)},
]


def get_available_slots(
    db: Session, 
    item_ids: list[str]
) -> list[dict]:
    """
    Retourne les créneaux disponibles pour une liste d'items du panier.
    
    Un créneau est disponible seulement si TOUS les items ont du stock 
    (current_quantity > 0 ou current_quantity is None = illimité).
    
    Args:
        db: Session SQLAlchemy
        item_ids: Liste des IDs des items (menu, boisson, bonus) - peut contenir None
    
    Returns:
        Liste de créneaux avec leur disponibilité:
        [
            {"slot": "07:00 - 08:00", "start": "07:00", "available": True},
            {"slot": "08:00 - 09:00", "start": "08:00", "available": False},
            ...
        ]
    """
    # Filtrer les IDs None
    valid_item_ids = [id for id in item_ids if id is not None]
    
    result = []
    
    for slot in TIME_SLOTS:
        slot_available = True
        
        # Si aucun item, tous les créneaux sont disponibles
        if valid_item_ids:
            for item_id in valid_item_ids:
                # Chercher la limite pour cet item et ce créneau
                limit = db.query(MenuItemLimit).filter(
                    MenuItemLimit.item_id == item_id,
                    MenuItemLimit.start_time <= slot["start"],
                    MenuItemLimit.end_time > slot["start"]
                ).first()
                
                # Si une limite existe et current_quantity <= 0, pas disponible
                if limit and limit.current_quantity is not None:
                    if limit.current_quantity <= 0:
                        slot_available = False
                        break
        
        result.append({
            "slot": slot["slot"],
            "start": slot["start"].strftime("%H:%M"),
            "available": slot_available
        })
    
    return result


def is_slot_available(
    db: Session,
    item_ids: list[str],
    slot_time: time
) -> bool:
    """
    Vérifie si un créneau spécifique est disponible pour les items donnés.
    
    Args:
        db: Session SQLAlchemy
        item_ids: Liste des IDs des items
        slot_time: L'heure du créneau (ex: time(8, 0) pour 8h)
    
    Returns:
        True si disponible, False sinon
    """
    valid_item_ids = [id for id in item_ids if id is not None]
    
    if not valid_item_ids:
        return True
    
    for item_id in valid_item_ids:
        limit = db.query(MenuItemLimit).filter(
            MenuItemLimit.item_id == item_id,
            MenuItemLimit.start_time <= slot_time,
            MenuItemLimit.end_time > slot_time
        ).first()
        
        if limit and limit.current_quantity is not None:
            if limit.current_quantity <= 0:
                return False
    
    return True
