
from datetime import datetime
from sqlalchemy.orm import Session

from src.reservations.models import Reservation, ReservationItem
from src.users.models import User
from src.core.exceptions import ReservationNotAllowedException, UserNotVerifiedException


def create_reservation(
    user_id: int,
    date_reservation: str,
    heure_reservation: str,
    habite_residence: bool,
    numero_chambre: str = None,
    numero_immeuble: str = None,
    adresse: str = None,
    phone: str = None,
    items: list = None,
    db: Session = None
) -> Reservation:
    """
    Crée une réservation avec items menu pour l'utilisateur.
    L'utilisateur doit être vérifié et cotisant BDE.
    """
    # Vérifier l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ReservationNotAllowedException("Utilisateur non trouvé")
    
    if not user.email_verified:
        raise UserNotVerifiedException("Email non vérifié")
    
    if not user.is_cotisant:
        raise ReservationNotAllowedException("Vous n'êtes pas cotisant BDE actif")
    
    # Calculer le total depuis les items
    from src.menu.models import MenuItem
    total_amount = 0.0
    reservation_items = []
    
    if items:
        for item_data in items:
            menu_item = db.query(MenuItem).filter(MenuItem.id == item_data.get('menu_item_id')).first()
            if not menu_item or not menu_item.available:
                raise ReservationNotAllowedException(f"Item menu {item_data.get('menu_item_id')} non disponible")
            
            quantity = item_data.get('quantity', 1)
            total_amount += menu_item.price * quantity
            reservation_items.append({
                'menu_item_id': menu_item.id,
                'quantity': quantity,
                'unit_price': menu_item.price
            })
    
    # Créer la réservation
    reservation = Reservation(
        user_id=user_id,
        date_reservation=date_reservation,
        heure_reservation=heure_reservation,
        habite_residence=habite_residence,
        numero_chambre=numero_chambre,
        numero_immeuble=numero_immeuble,
        adresse=adresse,
        phone=phone,
        total_amount=total_amount,
        status="confirmed",
        payment_status="pending"
    )
    
    try:
        db.add(reservation)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les items
        for item_data in reservation_items:
            reservation_item = ReservationItem(
                reservation_id=reservation.id,
                **item_data
            )
            db.add(reservation_item)
        
        db.commit()
        db.refresh(reservation)
    except Exception as e:
        db.rollback()
        raise ReservationNotAllowedException(f"Erreur création réservation: {str(e)}")
    
    return reservation
