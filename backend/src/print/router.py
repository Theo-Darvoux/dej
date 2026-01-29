from datetime import time
from typing import Optional
from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .markdown import generate_pdf_for_all_clients
from .schemas import PrintSummaryResponse, OrderCombo, OrderItem, OrdersListResponse
from ..users.router import get_current_user_from_cookie
from ..users.models import User
from ..core.exceptions import AdminException
from ..db.session import get_db

router = APIRouter(tags=["print"])


@router.get("/get_printPDF")
def get_ticket_pdf(
    start_time: str = Query("00:00"),
    end_time: str = Query("23:59"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # Vérifier si l'utilisateur est admin
    if current_user.user_type != "admin":
        raise AdminException()
    
    # Convertir les strings en objets time
    try:
        t_start = time.fromisoformat(start_time)
        t_end = time.fromisoformat(end_time)
    except ValueError:
        return Response(content="Format d'heure invalide (HH:MM)", status_code=400)

    # Récupérer les réservations filtrées
    reservations = db.query(User).filter(
        and_(
            User.payment_status == "completed",
            User.heure_reservation >= t_start,
            User.heure_reservation <= t_end
        )
    ).all()

    if not reservations:
        return Response(content="Aucune réservation trouvée pour ce créneau", status_code=404)

    # Générer le PDF directement
    pdf_bytes = generate_pdf_for_all_clients(reservations)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=tickets_{start_time}_{end_time}.pdf"
        }
    )


@router.get("/summary", response_model=PrintSummaryResponse)
def get_print_summary(
    start_time: str = Query("00:00"),
    end_time: str = Query("23:59"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    # Vérifier si l'utilisateur est admin
    if current_user.user_type != "admin":
        raise AdminException()

    # Convertir les strings en objets time
    try:
        t_start = time.fromisoformat(start_time)
        t_end = time.fromisoformat(end_time)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Format d'heure invalide (HH:MM)")



    # Récupérer les réservations filtrées
    reservations = db.query(User).filter(
        and_(
            User.payment_status == "completed",
            User.heure_reservation >= t_start,
            User.heure_reservation <= t_end
        )
    ).all()
    
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

    # Compter les types de commandes
    combos_dict = {}
    for res in reservations:
        menu_name = get_item_name(res.menu_id) or "Aucun"
        boisson_name = get_item_name(res.boisson_id) or "Aucune"
        bonus_name = get_item_name(res.bonus_id) or "Aucun"
        
        combo_key = (menu_name, boisson_name, bonus_name)
        combos_dict[combo_key] = combos_dict.get(combo_key, 0) + 1

    combos = [
        OrderCombo(menu=k[0], boisson=k[1], bonus=k[2], quantity=v)
        for k, v in combos_dict.items()
    ]

    return PrintSummaryResponse(
        start_time=start_time,
        end_time=end_time,
        combos=combos,
        total_orders=len(reservations)
    )


@router.get("/orders", response_model=OrdersListResponse)
def get_orders_list(
    start_time: str = Query("08:00"),
    end_time: str = Query("18:00"),
    payment_status: str = Query("all"),  # "completed", "pending", "all"
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Get paginated list of orders with filters"""
    if current_user.user_type != "admin":
        raise AdminException()

    try:
        t_start = time.fromisoformat(start_time)
        t_end = time.fromisoformat(end_time)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Format d'heure invalide (HH:MM)")

    from math import ceil

    # Build query with filters
    query = db.query(User).filter(
        and_(
            User.heure_reservation >= t_start,
            User.heure_reservation <= t_end
        )
    )

    # Payment status filter
    if payment_status == "completed":
        query = query.filter(User.payment_status == "completed")
    elif payment_status == "pending":
        query = query.filter(User.payment_status == "pending")
    # "all" = no additional filter

    # Get total count
    total = query.count()
    total_pages = ceil(total / per_page) if total > 0 else 1

    # Apply pagination
    offset = (page - 1) * per_page
    reservations = query.order_by(User.heure_reservation).offset(offset).limit(per_page).all()

    # Define get_item_name helper if not already defined in this scope? 
    # It's better to redefine or import it properly. Since we are in a function, let's just do it again cleanly.
    
    from src.menu.utils import load_menu_data
    menu_data_list = load_menu_data()
    
    def get_name(item_id):
        if not item_id: return None
        for cat in ["menus", "boissons", "extras"]:
            for item in menu_data_list.get(cat, []):
                if item["id"] == item_id:
                    return item["name"]
        return None

    # Build response
    orders = []
    for res in reservations:
        orders.append(OrderItem(
            id=res.id,
            prenom=res.prenom,
            nom=res.nom,
            heure_reservation=res.heure_reservation.strftime("%H:%M") if res.heure_reservation else "",
            menu=get_name(res.menu_id),
            boisson=get_name(res.boisson_id),
            bonus=get_name(res.bonus_id),
            payment_status=res.payment_status or "pending",
            is_maisel=res.adresse_if_maisel is not None,
            adresse=res.adresse
        ))

    return OrdersListResponse(
        orders=orders,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )
