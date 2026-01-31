from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import EmailStr
from typing import List, Optional

from src.reservations import schemas as res_schemas
from src.admin import schemas as admin_schemas
from src.users.router import get_current_user_from_cookie
from src.db.session import get_db
from src.users.models import User
from src.auth.schemas import UserResponse
from src.core.exceptions import AdminException

router = APIRouter()

# Whitelist of fields that admins can update
# SECURITY: payment_status is intentionally excluded - only the payment system can modify it
ALLOWED_UPDATE_FIELDS = {
    "prenom",
    "nom",
    "phone",
    "heure_reservation",
    "habite_residence",
    "adresse_if_maisel",
    "numero_if_maisel",
    "adresse",
    "special_requests",
    "menu_id",
    "boisson_id",
    "bonus_ids",
}

from src.menu.utils import load_menu_data

def require_admin(current_user):
    """Vérifie que l'utilisateur est admin. Lève AdminException sinon."""
    if not current_user or current_user.user_type != "admin":
        raise AdminException()
    return current_user

_menu_data_cache = None

def get_menu_data_cached():
    global _menu_data_cache
    if not _menu_data_cache:
        _menu_data_cache = load_menu_data()
    return _menu_data_cache

def get_item_details(item_id):
    if not item_id: return None
    data = get_menu_data_cached()
    for cat in ["menus", "boissons", "extras"]:
        for item in data.get(cat, []):
            if item["id"] == item_id:
                # Add item_type if missing, based on category
                item_copy = item.copy()
                if "item_type" not in item_copy:
                    if cat == "menus": item_copy["item_type"] = "menu"
                    elif cat == "boissons": item_copy["item_type"] = "boisson"
                    elif cat == "extras": item_copy["item_type"] = "upsell"
                return item_copy
    return None

def enrich_order(user):
    # Convert SQLAlchemy model to dict-like that Pydantic can parse
    # We can rely on Pydantic's from_attributes=True, but we need to inject the computed items
    user_dict = {
        c.name: getattr(user, c.name)
        for c in user.__table__.columns
    }

    # Inject items
    user_dict["menu_item"] = get_item_details(user.menu_id)
    user_dict["boisson_item"] = get_item_details(user.boisson_id)

    # Récupérer tous les extras
    extras_items = []
    if user.bonus_ids:
        for bonus_id in user.bonus_ids:
            details = get_item_details(bonus_id)
            if details:
                extras_items.append(details)
    user_dict["extras_items"] = extras_items

    return user_dict


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Récupère les infos de l'utilisateur connecté.
    Utilisé pour vérifier si l'utilisateur est toujours connecté.
    """
    require_admin(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/orders", response_model=List[admin_schemas.AdminOrderResponse])
async def list_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie),
    payment_status: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Liste toutes les commandes (utilisateurs avec réservations)"""
    require_admin(current_user)
    
    query = db.query(User).filter(
        User.menu_id.isnot(None) |
        User.boisson_id.isnot(None) |
        (User.bonus_ids.isnot(None) & (func.jsonb_array_length(User.bonus_ids) > 0)) |
        (User.payment_status == 'completed')
    )
    
    if payment_status:
        query = query.filter(User.payment_status == payment_status)
    if status:
        query = query.filter(User.status == status)
        
    orders = query.order_by(User.created_at.desc()).all()
    
    return [enrich_order(u) for u in orders]


@router.get("/orders/{user_id}", response_model=admin_schemas.AdminOrderResponse)
async def get_order(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Récupère une commande spécifique"""
    require_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    return enrich_order(user)


@router.patch("/orders/{user_id}", response_model=admin_schemas.AdminOrderResponse)
async def update_order(
    user_id: int,
    order_update: admin_schemas.AdminOrderUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Met à jour une commande"""
    require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    update_data = order_update.model_dump(exclude_unset=True)

    # Filter out fields not in whitelist (security: prevents payment_status modification)
    for field in list(update_data.keys()):
        if field not in ALLOWED_UPDATE_FIELDS:
            del update_data[field]

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return enrich_order(user)


@router.delete("/orders/{user_id}")
async def delete_order(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Supprime une commande (reset les champs de réservation)"""
    require_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Reset reservation fields instead of deleting the user
    user.menu_id = None
    user.boisson_id = None
    user.bonus_ids = []
    user.date_reservation = None
    user.heure_reservation = None
    user.total_amount = 0.0
    user.payment_status = None
    user.payment_intent_id = None
    user.payment_date = None
    user.payment_attempts = 0
    user.status = "confirmed"
    
    db.commit()
    return {"message": "Commande supprimée avec succès"}


@router.get("/users/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: EmailStr,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """recherche d'un utilisateur par mail"""
    require_admin(current_user)
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return UserResponse.model_validate(user)