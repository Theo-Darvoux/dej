from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, extract
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import EmailStr
from typing import List, Optional
from collections import Counter

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

from src.menu.utils import get_menu_data

def require_admin(current_user):
    """Vérifie que l'utilisateur est admin. Lève AdminException sinon."""
    if not current_user or current_user.user_type != "admin":
        raise AdminException()
    return current_user


def get_menu_data_cached():
    """Get cached menu data. Uses centralized cache from menu.utils."""
    return get_menu_data()

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
    """Supprime une commande et le compte utilisateur associé"""
    require_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Delete the user account completely
    db.delete(user)
    db.commit()
    
    return {"message": "Commande et compte utilisateur supprimés avec succès"}


@router.post("/orders/{user_id}/confirm-payment")
async def confirm_payment_manually(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Confirme manuellement le paiement d'une commande (pour paiements en espèces/liquide)"""
    require_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    if user.payment_status == "completed":
        raise HTTPException(status_code=400, detail="Le paiement est déjà confirmé")
    
    # Mark payment as completed manually
    from datetime import datetime, timezone
    user.payment_status = "completed"
    user.payment_date = datetime.now(timezone.utc)
    user.payment_intent_id = f"manual_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    db.commit()
    db.refresh(user)
    
    return {"message": "Paiement confirmé manuellement", "order": enrich_order(user)}


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


@router.get("/stats")
async def get_order_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Get order statistics for the admin dashboard.
    Returns stats on menus, drinks, extras, time slots, and order times.

    Optimized to use database aggregation instead of loading all orders into memory.
    """
    require_admin(current_user)

    # Get total count and revenue with single query
    base_stats = db.query(
        func.count(User.id).label('total_orders'),
        func.coalesce(func.sum(User.total_amount), 0).label('total_revenue')
    ).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None)
    ).first()

    total_orders = base_stats.total_orders or 0
    total_revenue = float(base_stats.total_revenue or 0)

    if total_orders == 0:
        return {
            "total_orders": 0,
            "menu_distribution": [],
            "drink_distribution": [],
            "extras_distribution": [],
            "time_slot_distribution": [],
            "order_hour_distribution": [],
            "total_extras": 0,
            "total_revenue": 0.0
        }

    menu_data = get_menu_data_cached()

    # Build ID-to-name lookup maps once (instead of per-item lookups)
    menu_names = {item["id"]: item["name"] for item in menu_data.get("menus", [])}
    drink_names = {item["id"]: item["name"] for item in menu_data.get("boissons", [])}
    extra_names = {item["id"]: item["name"] for item in menu_data.get("extras", [])}

    # Menu distribution - database aggregation
    menu_counts = db.query(
        User.menu_id,
        func.count(User.id).label('count')
    ).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None)
    ).group_by(User.menu_id).all()

    menu_distribution = sorted(
        [{"name": menu_names.get(row.menu_id, row.menu_id), "count": row.count}
         for row in menu_counts if row.menu_id],
        key=lambda x: -x["count"]
    )

    # Drink distribution - database aggregation
    drink_counts = db.query(
        User.boisson_id,
        func.count(User.id).label('count')
    ).filter(
        User.payment_status == "completed",
        User.boisson_id.isnot(None)
    ).group_by(User.boisson_id).all()

    drink_distribution = sorted(
        [{"name": drink_names.get(row.boisson_id, row.boisson_id), "count": row.count}
         for row in drink_counts if row.boisson_id],
        key=lambda x: -x["count"]
    )

    # Time slot distribution - database aggregation
    time_slot_counts = db.query(
        extract('hour', User.heure_reservation).label('hour'),
        func.count(User.id).label('count')
    ).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None),
        User.heure_reservation.isnot(None)
    ).group_by(extract('hour', User.heure_reservation)).all()

    time_slot_distribution = sorted(
        [{"slot": f"{int(row.hour)}h-{int(row.hour)+1}h", "count": row.count}
         for row in time_slot_counts if row.hour is not None],
        key=lambda x: int(x["slot"].split("h")[0])
    )

    # Order hour distribution - database aggregation
    order_hour_counts = db.query(
        extract('hour', User.created_at).label('hour'),
        func.count(User.id).label('count')
    ).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None),
        User.created_at.isnot(None)
    ).group_by(extract('hour', User.created_at)).all()

    order_hour_distribution = sorted(
        [{"hour": int(row.hour), "count": row.count}
         for row in order_hour_counts if row.hour is not None],
        key=lambda x: x["hour"]
    )

    # Extras distribution - need to fetch bonus_ids and aggregate in Python
    # (JSON array aggregation is complex across databases)
    orders_with_extras = db.query(User.bonus_ids).filter(
        User.payment_status == "completed",
        User.bonus_ids.isnot(None)
    ).all()

    extras_counts = Counter()
    for (bonus_ids,) in orders_with_extras:
        if bonus_ids:
            for extra_id in bonus_ids:
                extras_counts[extra_id] += 1

    total_extras = sum(extras_counts.values())
    extras_distribution = sorted(
        [{"name": extra_names.get(extra_id, extra_id), "count": count}
         for extra_id, count in extras_counts.items()],
        key=lambda x: -x["count"]
    )

    return {
        "total_orders": total_orders,
        "menu_distribution": menu_distribution,
        "drink_distribution": drink_distribution,
        "extras_distribution": extras_distribution,
        "time_slot_distribution": time_slot_distribution,
        "order_hour_distribution": order_hour_distribution,
        "total_extras": total_extras,
        "total_revenue": round(total_revenue, 2)
    }