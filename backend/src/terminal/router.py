from datetime import time, datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .schemas import TerminalOrder, TerminalOrdersResponse
from ..users.router import get_current_user_from_cookie
from ..users.models import User
from ..core.exceptions import AdminException
from ..db.session import get_db

router = APIRouter(tags=["terminal"])

# Paris timezone
PARIS_TZ = ZoneInfo("Europe/Paris")


@router.get("/orders", response_model=TerminalOrdersResponse)
def get_terminal_orders(
    auto_hour: bool = Query(True),  # Auto-detect current hour
    hour: int = Query(None, ge=8, le=17),  # Manual hour override
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Get orders for terminal kitchen display - only paid orders for current hour"""
    if current_user.user_type != "admin":
        raise AdminException()

    # Determine hour to filter
    if auto_hour or hour is None:
        paris_now = datetime.now(PARIS_TZ)
        current_hour = paris_now.hour
    else:
        current_hour = hour

    # Clamp to valid range
    if current_hour < 8:
        current_hour = 8
    elif current_hour > 17:
        current_hour = 17

    # Time range for this hour
    t_start = time(hour=current_hour, minute=0)
    t_end = time(hour=current_hour, minute=59)

    # Query paid orders for this hour
    reservations = db.query(User).filter(
        and_(
            User.payment_status == "completed",
            User.heure_reservation >= t_start,
            User.heure_reservation <= t_end
        )
    ).order_by(User.heure_reservation).all()

    # Helper to resolve item name
    from src.menu.utils import load_menu_data
    menu_data = load_menu_data()
    
    def get_item_name(item_id):
        if not item_id: return None
        for cat in ["menus", "boissons", "extras"]:
            for item in menu_data.get(cat, []):
                if item["id"] == item_id:
                    return item["name"]
        return None

    # Build response
    orders = []
    for res in reservations:
        # Récupérer tous les extras
        extras_names = []
        if res.bonus_ids:
            for bonus_id in res.bonus_ids:
                name = get_item_name(bonus_id)
                if name:
                    extras_names.append(name)

        orders.append(TerminalOrder(
            id=res.id,
            prenom=res.prenom,
            nom=res.nom,
            is_maisel=res.adresse_if_maisel is not None,
            batiment=res.adresse_if_maisel.value if res.adresse_if_maisel else None,
            menu=get_item_name(res.menu_id),
            boisson=get_item_name(res.boisson_id),
            extras=extras_names
        ))

    return TerminalOrdersResponse(
        orders=orders,
        current_hour=current_hour,
        total=len(orders)
    )
