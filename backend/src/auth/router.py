from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.auth import schemas, service
from src.core.exceptions import UserNotVerifiedException

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
    user_id, is_cotisant = await service.verify_code(
        request_data.email,
        request_data.code,
        db,
        client_ip=request.client.host if request.client else None
    )
    
    # Générer tokens
    tokens = await service.get_tokens(user_id, request_data.email)
    
    # Setter tokens en cookies httpOnly
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,  # À adapter selon env (dev vs prod)
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 jours
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
    
    return schemas.LogoutResponse(message="Déconnecté avec succès")

