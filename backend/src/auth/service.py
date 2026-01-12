import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.users.models import User
from src.core.config import settings
from src.core.security import verify_with_bde, create_access_token, create_refresh_token
from src.core.exceptions import (
    InvalidCredentialsException,
    CodeExpiredException,
    BDENotCotisantException,
    EmailSendFailedException,
    UserNotVerifiedException
)
from src.mail import send_verification_email
from src.auth.schemas import TokenResponse


async def request_verification_code(email: str, db: Session) -> bool:
    """
    Génère et envoie un code de vérification par email.
    Retourne True si succès, lance exception sinon.
    """
    # Générer code à 6 chiffres
    code = ''.join(random.choices(string.digits, k=settings.EMAIL_CODE_LENGTH))
    
    # Trouver ou créer utilisateur
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
    
    # Stocker le code avec timestamp
    user.verification_code = code
    user.code_created_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise EmailSendFailedException("Erreur base de données")
    
    # Envoyer email
    try:
        await send_verification_email(email, code)
    except Exception as e:
        # Nettoyer le code si l'envoi échoue
        user.verification_code = None
        user.code_created_at = None
        db.commit()
        raise EmailSendFailedException(f"Impossible d'envoyer l'email: {str(e)}")
    
    return True


async def verify_code(email: str, code: str, db: Session) -> tuple[int, bool]:
    """
    Vérifie le code et retourne (user_id, is_cotisant).
    Lance une exception si invalide/expiré.
    Vérifie aussi avec BDE API.
    """
    # Chercher utilisateur
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    # Vérifier code
    if not user.verification_code or user.verification_code != code:
        raise InvalidCredentialsException("Code invalide")
    
    # Vérifier expiration (15 min)
    if not user.code_created_at:
        raise CodeExpiredException()
    
    # Ensure code_created_at is timezone-aware for comparison
    code_created_at = user.code_created_at
    if code_created_at.tzinfo is None:
        code_created_at = code_created_at.replace(tzinfo=timezone.utc)
    
    time_diff = datetime.now(timezone.utc) - code_created_at
    if time_diff > timedelta(minutes=settings.EMAIL_CODE_EXPIRE_MINUTES):
        user.verification_code = None
        user.code_created_at = None
        db.commit()
        raise CodeExpiredException()
    
    # Vérifier avec BDE API
    #is_cotisant = await verify_with_bde(email) #TODO
    is_cotisant = True  # TODO: Supprimer cette ligne après intégration BDE

    # Extraire prénom/nom depuis l'email (format prenom.nom@...)
    try:
        local_part = email.split("@")[0]
        parts = [p for p in local_part.replace("_", ".").replace("-", ".").split(".") if p]
        if len(parts) >= 2:
            prenom_raw, nom_raw = parts[0], parts[1]
            user.prenom = prenom_raw.strip().capitalize()
            user.nom = nom_raw.strip().capitalize()
    except Exception:
        # Ne bloque pas la vérification si parsing échoue
        pass

    # Marquer email comme vérifié
    user.email_verified = True
    user.is_cotisant = is_cotisant
    user.cotisant_checked_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise InvalidCredentialsException("Erreur lors de la vérification")
    
    return user.id, is_cotisant


async def get_tokens(user_id: int, email: str) -> TokenResponse:
    """Génère access et refresh tokens JWT"""
    access_token = create_access_token(email, user_id)
    refresh_token = create_refresh_token(email, user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=email
    )


async def refresh_access_token(refresh_token: str, db: Session) -> TokenResponse:
    """Génère un nouveau access token à partir du refresh token"""
    from core.security import decode_token
    
    token_data = decode_token(refresh_token)
    
    # Vérifier que c'est bien un refresh token
    try:
        from jose import jwt
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("Token invalide")
    except Exception:
        raise InvalidCredentialsException("Token invalide")
    
    # Récupérer l'utilisateur pour mettre à jour
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    access_token = create_access_token(token_data.email, token_data.user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email
    )


def get_user_by_token(token: str, db: Session) -> User:
    """Récupère l'utilisateur à partir d'un token JWT"""
    from core.security import decode_token
    
    token_data = decode_token(token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    if not user.email_verified:
        raise UserNotVerifiedException()
    
    return user