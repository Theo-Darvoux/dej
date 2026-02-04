from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth import schemas, service
from src.core.exceptions import UserNotVerifiedException
from src.core.rate_limit import rate_limiter

router = APIRouter()


@router.post("/request-code", response_model=schemas.RequestCodeResponse)
async def request_code(
    request: schemas.RequestCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Étape 1: L'utilisateur rentre son email
    - Génère un code à 6 chiffres/lettres
    - Envoie l'email avec code et lien
    - Crée/met à jour l'utilisateur en DB
    """
    # Rate limit by email: 3 requests per 15 minutes
    await rate_limiter.check(f"email:{request.email}", max_requests=3, window_seconds=900)

    await service.request_verification_code(request.email, db)
    
    return schemas.RequestCodeResponse(
        message=f"Code de vérification envoyé à {request.email}",
        email=request.email
    )


@router.post("/verify", response_model=schemas.VerifyCodeResponse)
async def verify_code(
    request_data: schemas.VerifyCodeRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Étape 2: L'utilisateur clique sur le lien ou rentre le code
    - Vérifie le code (doit être < 15 min)
    - Vérifie avec BDE API si cotisant
    - Émet JWT httpOnly + refresh token
    - Retourne is_cotisant pour guider vers l'étape suivante
    """
    # Rate limit by email: 5 verification attempts per 1 minutes
    await rate_limiter.check(f"verify:{request_data.email}", max_requests=5, window_seconds=60)

    user_id, is_cotisant = await service.verify_code(
        request_data.email,
        request_data.code,
        db,
        client_ip=request.client.host if request.client else None
    )
    
    # Générer tokens
    tokens = await service.get_tokens(user_id, request_data.email)
    
    # Setter tokens en cookies httpOnly
    from src.core.config import settings
    is_production = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=is_production,  # True en prod (HTTPS), False en dev (HTTP)
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # En secondes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7 jours en secondes
    )
    
    return schemas.VerifyCodeResponse(
        message="Email vérifié avec succès",
        is_verified=True,
        is_cotisant=is_cotisant
    )




@router.post("/logout", response_model=schemas.LogoutResponse)
async def logout(response: Response):
    """
    Logout: efface les cookies
    """
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return schemas.LogoutResponse(message="Déconnecté avec succès")


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Rafraîchit l'access token en utilisant le refresh token
    """
    from src.core.security import decode_token
    
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token manquant"
        )
    
    # Décoder et valider le refresh token
    token_data = decode_token(refresh_token, expected_type="refresh")
    
    # Vérifier que l'utilisateur existe toujours
    user = service.get_user_by_token(refresh_token, db, expected_type="refresh")
    
    if not user or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur invalide ou non vérifié"
        )
    
    # Générer nouveaux tokens
    tokens = await service.get_tokens(user.id, user.email)
    
    # Mettre à jour les cookies
    from src.core.config import settings
    is_production = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return tokens

