from datetime import datetime
from sqlalchemy.orm import Session

from src.users.models import User
from src.core.exceptions import ReservationNotAllowedException, UserNotVerifiedException


def create_reservation(
    user_id: int,
    date_reservation: str,
    heure_reservation: str,
    habite_residence: bool,
    numero_chambre: str = None,
    adresse: str = None,
    phone: str = None,
    menu: str = None,
    boisson: str = None,
    bonus: str = None,
    db: Session = None
) -> User:
    """
    Crée une réservation en mettant à jour les données utilisateur.
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
    
    # Mettre à jour les données de réservation
    user.date_reservation = date_reservation
    user.heure_reservation = heure_reservation
    user.habite_residence = habite_residence
    user.numero_if_maisel = numero_chambre
    user.adresse = adresse if not habite_residence else None
    user.phone = phone
    user.menu = menu
    user.boisson = boisson
    user.bonus = bonus
    user.status = "confirmed"
    user.payment_status = "pending"
    
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise ReservationNotAllowedException(f"Erreur création réservation: {str(e)}")
    
    return user
