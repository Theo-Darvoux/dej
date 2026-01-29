from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from src.db.session import get_db
from src.reservations.router import get_current_user_from_cookie
from src.users.models import User

router = APIRouter()


@router.get("/me")
async def get_current_user_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Récupérer les détails complets de l'utilisateur connecté et sa commande"""
    # Re-fetch user with items loaded
    # Fetch user
    user = db.query(User).filter(User.id == current_user.id).first()
    
    has_active_order = user.menu_id is not None or user.boisson_id is not None or user.bonus_id is not None
    
    # Helper to resolve item name/price
    from src.menu.utils import load_menu_data
    menu_data = load_menu_data()
    
    def get_item_details(item_id):
        if not item_id: return None
        for cat in ["menus", "boissons", "extras"]:
            for item in menu_data.get(cat, []):
                if item["id"] == item_id:
                    return item
        return None

    menu_details = get_item_details(user.menu_id)
    boisson_details = get_item_details(user.boisson_id)
    bonus_details = get_item_details(user.bonus_id)

    return {
        "id": user.id,
        "email": user.email,
        "prenom": user.prenom,
        "nom": user.nom,
        "payment_status": user.payment_status,
        "has_active_order": has_active_order,
        "order": {
            "menu": menu_details["name"] if menu_details else None,
            "boisson": boisson_details["name"] if boisson_details else None,
            "bonus": bonus_details["name"] if bonus_details else None,
            "total_amount": user.total_amount,
            "heure_reservation": user.heure_reservation.strftime("%H:%M") if user.heure_reservation else None,
            "adresse": user.adresse if not user.habite_residence else f"Maisel {user.adresse_if_maisel.value if user.adresse_if_maisel else ''} - Ch {user.numero_if_maisel}",
            "phone": user.phone
        } if has_active_order else None
    }


@router.get("/order/status/{status_token}")
async def get_order_status(
    status_token: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer le statut d'une commande via un token unique.
    Endpoint public (pas d'authentification requise).
    """
    user = db.query(User).filter(User.status_token == status_token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commande non trouvée"
        )
    
    # Construire l'adresse
    if user.habite_residence:
        adresse = f"Maisel {user.adresse_if_maisel.value if user.adresse_if_maisel else ''} - Ch {user.numero_if_maisel}"
    else:
        adresse = user.adresse or "Non renseignée"
    
    
    # Helper to resolve item name/price
    from src.menu.utils import load_menu_data
    menu_data = load_menu_data()
    
    def get_item_details(item_id):
        if not item_id: return None
        for cat in ["menus", "boissons", "extras"]:
            for item in menu_data.get(cat, []):
                if item["id"] == item_id:
                    return item
        return None
        
    menu_details = get_item_details(user.menu_id)
    boisson_details = get_item_details(user.boisson_id)
    bonus_details = get_item_details(user.bonus_id)
    
    # Construire la liste des produits
    produits = []
    if menu_details:
        produits.append({
            "name": menu_details["name"],
            "price": menu_details.get("price", 0),
            "category": "Menu"
        })
    if boisson_details:
        produits.append({
            "name": boisson_details["name"],
            "price": boisson_details.get("price", 0),
            "category": "Boisson"
        })
    if bonus_details:
        produits.append({
            "name": bonus_details["name"],
            "price": bonus_details.get("price", 0),
            "category": "Supplément"
        })
    
    return {
        "prenom": user.prenom,
        "nom": user.nom,
        "status": user.status,
        "payment_status": user.payment_status,
        "date_reservation": "2026-02-07",  # Date fixe de l'événement
        "heure_reservation": user.heure_reservation.strftime("%H:%M") if user.heure_reservation else None,
        "adresse": adresse,
        "phone": user.phone,
        "special_requests": user.special_requests,
        "produits": produits,
        "total_amount": user.total_amount,
        "payment_date": user.payment_date.isoformat() if user.payment_date else None,
        "contacts": {
            "responsable1": {
                "name": "Théo DARVOUX",
                "email": "theo.darvoux@telecom-sudparis.eu"
            },
            "responsable2": {
                "name": "Solène CHAMPION",
                "email": "solene.champion@telecom-sudparis.eu"
            }
        }
    }

