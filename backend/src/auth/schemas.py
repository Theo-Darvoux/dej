from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    """Réponse token (envoyé dans cookies, infos en body)"""
    access_token: str
    user_id: int
    email: str


class RequestCodeRequest(BaseModel):
    """Demande d'envoi de code de vérification"""
    email: EmailStr


class RequestCodeResponse(BaseModel):
    """Réponse envoi code"""
    message: str
    email: str


class VerifyCodeRequest(BaseModel):
    """Vérification de code/lien"""
    email: EmailStr
    code: str


class VerifyCodeResponse(BaseModel):
    """Réponse vérification code"""
    message: str
    is_verified: bool
    is_cotisant: bool  # Après vérif BDE




class LogoutResponse(BaseModel):
    """Réponse logout"""
    message: str


class UserResponse(BaseModel):
    """Infos utilisateur"""
    id: int
    email: str
    prenom: Optional[str]
    nom: Optional[str]
    email_verified: bool
    is_cotisant: bool
    created_at: datetime

    class Config:
        from_attributes = True
