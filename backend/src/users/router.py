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
    user = db.query(User).options(
        joinedload(User.menu_item),
        joinedload(User.boisson_item),
        joinedload(User.bonus_item)
    ).filter(User.id == current_user.id).first()
    
    has_active_order = user.menu_id is not None or user.boisson_id is not None or user.bonus_id is not None
    
    return {
        "id": user.id,
        "email": user.email,
        "prenom": user.prenom,
        "nom": user.nom,
        "payment_status": user.payment_status,
        "has_active_order": has_active_order,
        "order": {
            "menu": user.menu_item.name if user.menu_item else None,
            "boisson": user.boisson_item.name if user.boisson_item else None,
            "bonus": user.bonus_item.name if user.bonus_item else None,
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
    user = db.query(User).options(
        joinedload(User.menu_item),
        joinedload(User.boisson_item),
        joinedload(User.bonus_item)
    ).filter(User.status_token == status_token).first()
    
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
    
    # Construire la liste des produits
    produits = []
    if user.menu_item:
        produits.append({
            "name": user.menu_item.name,
            "price": user.menu_item.price,
            "category": "Menu"
        })
    if user.boisson_item:
        produits.append({
            "name": user.boisson_item.name,
            "price": user.boisson_item.price,
            "category": "Boisson"
        })
    if user.bonus_item:
        produits.append({
            "name": user.bonus_item.name,
            "price": user.bonus_item.price,
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

