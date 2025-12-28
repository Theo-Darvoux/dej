
from datetime import datetime
from sqlalchemy.orm import Session

from src.reservations.models import Reservation
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
    db: Session = None
) -> Reservation:
    """
    Crée une réservation pour l'utilisateur.
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
    
    # Créer la réservation
    reservation = Reservation(
        user_id=user_id,
        date_reservation=date_reservation,
        heure_reservation=heure_reservation,
        habite_residence=habite_residence,
        numero_chambre=numero_chambre,
        numero_immeuble=numero_immeuble,
        adresse=adresse,
        status="confirmed",
        payment_status="pending"
    )
    
    try:
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
    except Exception as e:
        db.rollback()
        raise ReservationNotAllowedException(f"Erreur création réservation: {str(e)}")
    
    return reservation
