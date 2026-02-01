from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import httpx
from fastapi import HTTPException, status
from src.core.config import settings


class TokenData:
    """Données d'un token JWT"""
    def __init__(self, email: str, user_id: Optional[int] = None):
        self.email = email
        self.user_id = user_id


def create_access_token(email: str, user_id: int) -> str:
    """Crée un JWT access token"""
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(email: str, user_id: int) -> str:
    """Crée un JWT refresh token"""
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str, expected_type: str = "access") -> TokenData:
    """Décode et valide un JWT"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        return TokenData(email=email, user_id=user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )


async def verify_with_bde(email: str) -> bool:
    """
    Vérifie avec l'API BDE si l'utilisateur est cotisant actif.
    
    Retourne True si 200 OK (cotisant), False sinon.
    Lance une exception HTTPException si erreur.
    """
    if not settings.BDE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BDE API key non configurée"
        )
    
    headers = {
        "Authorization": f"Bearer {settings.BDE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"email": email}
    
    try:
        async with httpx.AsyncClient(timeout=settings.BDE_API_TIMEOUT) as client:
            response = await client.post(
                f"{settings.BDE_API_URL}/api/is_cotisant",
                json=payload,
                headers=headers
            )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="BDE API: clé invalide/inactive"
            )
        elif response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="BDE API: accès refusé (scope insuffisant)"
            )
        elif response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BDE API: email invalide"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"BDE API: erreur {response.status_code}"
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BDE API: timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur vérification BDE: {str(e)}"
        )
