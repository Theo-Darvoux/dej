from fastapi import APIRouter, HTTPException, Depends, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, time, date

from src.db.session import get_db
from src.users.models import User
from src.users.schemas import UserWithReservationResponse
from src.auth.schemas import UserResponse
from src.auth.service import get_user_by_token
from src.menu.models import MenuItem

router = APIRouter()


def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Dépendance pour récupérer l'utilisateur depuis le cookie"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Non connecté")
    
    user = get_user_by_token(access_token, db)
    return user




@router.get("/me", response_model=UserWithReservationResponse)
def get_current_user_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Récupérer les détails complets de l'utilisateur connecté"""
    return current_user


