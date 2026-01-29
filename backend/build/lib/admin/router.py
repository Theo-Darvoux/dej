from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import EmailStr

from src.reservations import schemas
from src.users.router import get_current_user_from_cookie
from src.db.session import get_db
from src.users.models import User
from src.auth.schemas import UserResponse
from src.core.exceptions import AdminException

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Récupère les infos de l'utilisateur connecté.
    Utilisé pour vérifier si l'utilisateur est toujours connecté.
    """

    if current_user.admin != "admin":
        raise AdminException()
    else:
        return UserResponse.model_validate(current_user)


@router.get("/users/{email}", response_model=UserResponse)
async def get_user(
    email: EmailStr,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """Récupère un utilisateur par email (admin seulement)
    Utilisé par les admins pour vérifier les comptes des utilisateurs.
    """
    if current_user.admin != "admin":
        raise AdminException()
    else:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        return UserResponse.model_validate(user)



    
@router.get("/reservations/{reservation_id}", response_model=schemas.ReservationResponse)
async def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Récupère une réservation spécifique de l'utilisateur.
    Utilisé par les admins pour vérifier les réservations des utilisateurs.
    """
    if current_user.admin != "admin":
        raise AdminException()
    else:
        from reservations.models import Reservation
        
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.user_id == current_user.id
        ).first()
        
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Réservation non trouvée"
            )
        
        return schemas.ReservationResponse.model_validate(reservation)