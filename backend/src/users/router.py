from fastapi import APIRouter, HTTPException, Depends, Cookie
from sqlalchemy.orm import Session
from typing import Optional

from src.db.session import get_db
from src.users.models import User
from src.auth.schemas import UserResponse
from src.auth.service import get_user_by_token

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

