from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, extract
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import EmailStr
from typing import List, Optional
from collections import Counter
from datetime import date, time, datetime, timezone

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


def get_item_by_name(name: str, category: str = None):
    """Find a menu item by name. Optionally filter by category (menus, boissons, extras)."""
    if not name:
        return None
    data = get_menu_data_cached()
    categories = [category] if category else ["menus", "boissons", "extras"]
    for cat in categories:
        for item in data.get(cat, []):
            if item["name"].lower() == name.lower():
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

    # Location distribution (MAISEL vs Evry)
    maisel_count = db.query(func.count(User.id)).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None),
        User.adresse_if_maisel.isnot(None)
    ).scalar() or 0
    
    evry_count = db.query(func.count(User.id)).filter(
        User.payment_status == "completed",
        User.menu_id.isnot(None),
        User.adresse_if_maisel.is_(None)
    ).scalar() or 0
    
    location_distribution = [
        {"name": "MAISEL", "count": maisel_count},
        {"name": "Evry", "count": evry_count}
    ]

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
            "location_distribution": [],
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
        "location_distribution": location_distribution,
        "total_extras": total_extras,
        "total_revenue": round(total_revenue, 2)
    }


@router.post("/orders/create", response_model=admin_schemas.AdminOrderResponse)
async def create_order(
    order_data: admin_schemas.AdminCreateOrder,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Crée manuellement une commande (admin uniquement, aucune validation)"""
    require_admin(current_user)

    # Look up menu item by name
    menu_item = get_item_by_name(order_data.menu, "menus")
    if not menu_item:
        raise HTTPException(status_code=400, detail=f"Menu introuvable: {order_data.menu}")

    # Look up drink by name (optional)
    boisson_item = None
    if order_data.boisson:
        boisson_item = get_item_by_name(order_data.boisson, "boissons")
        if not boisson_item:
            raise HTTPException(status_code=400, detail=f"Boisson introuvable: {order_data.boisson}")

    # Look up extras by name (optional)
    bonus_ids = []
    if order_data.extras:
        for extra_name in order_data.extras:
            extra_item = get_item_by_name(extra_name, "extras")
            if not extra_item:
                raise HTTPException(status_code=400, detail=f"Extra introuvable: {extra_name}")
            bonus_ids.append(extra_item["id"])

    # Calculate total
    total = float(menu_item.get("price", 0))
    if boisson_item:
        total += float(boisson_item.get("price", 0))
    for bid in bonus_ids:
        details = get_item_details(bid)
        if details:
            total += float(details.get("price", 0))

    # Normalize email
    email = order_data.email.strip().lower()
    local_part = email.split("@")[0] if "@" in email else email
    normalized = local_part.replace("_", ".") + ("@" + email.split("@")[1] if "@" in email else "")

    # Parse time
    try:
        h, m = order_data.heure_reservation.split(":")
        heure = time(int(h), int(m))
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Format heure invalide (HH:MM attendu)")

    # Check if user with same email exists - update instead of duplicate
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        existing_user.menu_id = menu_item["id"]
        existing_user.boisson_id = boisson_item["id"] if boisson_item else None
        existing_user.bonus_ids = bonus_ids if bonus_ids else []
        existing_user.heure_reservation = heure
        existing_user.date_reservation = date(2026, 2, 7)
        existing_user.habite_residence = order_data.habite_residence
        existing_user.adresse_if_maisel = order_data.adresse_if_maisel if order_data.habite_residence else None
        existing_user.numero_if_maisel = int(order_data.numero_chambre) if order_data.numero_chambre and order_data.habite_residence else None
        existing_user.adresse = order_data.adresse if not order_data.habite_residence else None
        existing_user.phone = order_data.phone
        existing_user.special_requests = order_data.special_requests
        existing_user.prenom = order_data.prenom
        existing_user.nom = order_data.nom
        existing_user.total_amount = total
        existing_user.email_verified = True
        existing_user.is_cotisant = True
        existing_user.status = "confirmed"
        db.commit()
        db.refresh(existing_user)
        return enrich_order(existing_user)

    # Create new user
    new_user = User(
        email=email,
        normalized_email=normalized,
        prenom=order_data.prenom,
        nom=order_data.nom,
        email_verified=True,
        is_cotisant=True,
        menu_id=menu_item["id"],
        boisson_id=boisson_item["id"] if boisson_item else None,
        bonus_ids=bonus_ids if bonus_ids else [],
        heure_reservation=heure,
        date_reservation=date(2026, 2, 7),
        habite_residence=order_data.habite_residence,
        adresse_if_maisel=order_data.adresse_if_maisel if order_data.habite_residence else None,
        numero_if_maisel=int(order_data.numero_chambre) if order_data.numero_chambre and order_data.habite_residence else None,
        adresse=order_data.adresse if not order_data.habite_residence else None,
        phone=order_data.phone,
        special_requests=order_data.special_requests,
        total_amount=total,
        payment_status="pending",
        status="confirmed",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return enrich_order(new_user)


@router.post("/orders/{user_id}/checkout-link")
async def generate_checkout_link(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Génère un lien de paiement HelloAsso pour une commande (admin uniquement)"""
    require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Commande non trouvée")

    if user.payment_status == "completed":
        raise HTTPException(status_code=400, detail="Le paiement est déjà confirmé")

    from src.payments import helloasso_service
    from src.core.config import settings

    # Build redirect URLs
    redirect_base = settings.HELLOASSO_REDIRECT_BASE_URL
    if not redirect_base:
        redirect_base = settings.FRONTEND_URL or "http://localhost:5173"
    redirect_base = redirect_base.rstrip('/')

    return_url = f"{redirect_base}/payment/success"
    error_url = f"{redirect_base}/payment/error"
    back_url = f"{redirect_base}/order"

    payer_first = user.prenom if user.prenom and len(user.prenom) >= 2 else "Admin"
    payer_last = user.nom if user.nom and len(user.nom) >= 2 else "Order"

    metadata = {"reservation_id": user.id}

    result = await helloasso_service.create_checkout_intent(
        payer_email=user.email,
        payer_first_name=payer_first,
        payer_last_name=payer_last,
        return_url=return_url,
        error_url=error_url,
        back_url=back_url,
        metadata=metadata,
        contains_donation=False
    )

    checkout_intent_id = result["id"]
    redirect_url = result["redirectUrl"]

    # Store on user
    user.payment_intent_id = checkout_intent_id
    user.checkout_redirect_url = redirect_url
    user.checkout_created_at = datetime.now(timezone.utc)
    db.commit()

    return {"redirect_url": redirect_url, "checkout_intent_id": checkout_intent_id}