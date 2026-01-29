from datetime import time, datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
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
    reservations = db.query(User).options(
        joinedload(User.menu_item),
        joinedload(User.boisson_item),
        joinedload(User.bonus_item)
    ).filter(
        and_(
            User.payment_status == "completed",
            User.heure_reservation >= t_start,
            User.heure_reservation <= t_end
        )
    ).order_by(User.heure_reservation).all()

    # Build response
    orders = []
    for res in reservations:
        orders.append(TerminalOrder(
            id=res.id,
            prenom=res.prenom,
            nom=res.nom,
            is_maisel=res.adresse_if_maisel is not None,
            batiment=res.adresse_if_maisel.value if res.adresse_if_maisel else None,
            menu=res.menu_item.name if res.menu_item else None,
            boisson=res.boisson_item.name if res.boisson_item else None,
            bonus=res.bonus_item.name if res.bonus_item else None
        ))

    return TerminalOrdersResponse(
        orders=orders,
        current_hour=current_hour,
        total=len(orders)
    )
