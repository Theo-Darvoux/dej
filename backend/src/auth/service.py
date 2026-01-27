import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.users.models import User
from src.core.config import settings
from src.core.security import verify_with_bde, create_access_token
from src.core.exceptions import (
    InvalidCredentialsException,
    CodeExpiredException,
    BDENotCotisantException,
    EmailSendFailedException,
    UserNotVerifiedException,
    InvalidEmailException
)
from src.mail import send_verification_email
from src.auth.schemas import TokenResponse



ALLOWED_DOMAINS = [
    "imt-bs.eu",
    "imtbs-tsp.eu",
    "it-sudparis.eu",
    "telecom-sudparis.eu"
]


def normalize_email(email: str) -> tuple[str, str]:
    """
    Normalise l'email et valide le format.
    Retourne (email_pour_envoi, identite_unique).
    L'identite_unique est au format prenom.nom (sans domaine).
    Lance InvalidEmailException si invalide.
    """
    email = email.strip().lower()
    
    if "@" not in email:
        raise InvalidEmailException("Format d'email invalide")
    
    local_part, domain = email.split("@", 1)
    
    if domain not in ALLOWED_DOMAINS:
        raise InvalidEmailException(f"Domaine {domain} non autorisé")
    
    # Bloquer les alias (+truc)
    if "+" in local_part:
        raise InvalidEmailException("Les alias (+) ne sont pas autorisés")
    
    # Vérifier le format prenom.nom ou prenom_nom
    # Pour l'identité (normalisé), on remplace _ par .
    # On veut au moins un séparateur . ou _
    if "." not in local_part and "_" not in local_part:
        raise InvalidEmailException("L'email doit être au format prenom.nom ou prenom_nom")
    
    # Remplacer _ par . pour l'identité unique
    identity = local_part.replace("_", ".")
    
    # Vérifier qu'il y a bien au moins deux parties (prenom et nom)
    parts = [p for p in identity.split(".") if p]
    if len(parts) < 2:
        raise InvalidEmailException("L'email doit contenir un prénom et un nom séparés par un point ou un underscore")
    
    # L'identité unique ne contient pas le domaine pour permettre la déduplication cross-domaine
    # On garde delivery_email tel quel pour l'envoi (avec son domaine original)
    delivery_email = f"{local_part}@{domain}"
    
    return delivery_email, identity


async def request_verification_code(email: str, db: Session) -> bool:
    """
    Génère et envoie un code de vérification par email.
    Retourne True si succès, lance exception sinon.
    """
    # Valider et normaliser l'email
    delivery_email, identity = normalize_email(email)
    
    # Générer code à 6 caractères alphanumériques
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choices(chars, k=settings.EMAIL_CODE_LENGTH))
    
    # Trouver ou créer utilisateur par normalized_email (qui contient maintenant l'identité prenom.nom)
    user = db.query(User).filter(User.normalized_email == identity).first()
    if not user:
        user = User(email=delivery_email, normalized_email=identity)
        db.add(user)
    else:
        # Mettre à jour l'email de livraison si nécessaire (le dernier utilisé)
        user.email = delivery_email
    
    # Stocker le code avec timestamp
    user.verification_code = code
    user.code_created_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise EmailSendFailedException("Erreur base de données")
    
    # Envoyer email (utiliser delivery_email)
    try:
        #await send_verification_email(delivery_email, code)
        pass  # TODO: remettre l'envoi d'email en prod
    except Exception as e:
        # Nettoyer le code si l'envoi échoue
        user.verification_code = None
        user.code_created_at = None
        db.commit()
        raise EmailSendFailedException(f"Impossible d'envoyer l'email: {str(e)}")
    
    return True


async def verify_code(email: str, code: str, db: Session, client_ip: str = None) -> tuple[int, bool]:
    """
    Vérifie le code et retourne (user_id, is_cotisant).
    Lance une exception si invalide/expiré.
    Vérifie aussi avec BDE API.
    """
    
    # Valider et normaliser
    _, identity = normalize_email(email)
    
    # Chercher utilisateur par normalized_email (identité unique)
    user = db.query(User).filter(User.normalized_email == identity).first()
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    #"""# TODO DEBUT
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
    #""" #TODO FIN
    # Vérifier avec BDE API
    is_cotisant = await verify_with_bde(email)
    #is_cotisant=True # TODO: à supprimer

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
        user.prenom = ""
        user.nom = ""
        pass

    # Marquer email comme vérifié et log IP
    user.email_verified = True
    user.is_cotisant = is_cotisant
    user.cotisant_checked_at = datetime.now(timezone.utc)
    if client_ip:
        user.last_ip = client_ip
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise InvalidCredentialsException("Erreur lors de la vérification")
    
    return user.id, is_cotisant


async def get_tokens(user_id: int, email: str) -> TokenResponse:
    """Génère access token JWT"""
    access_token = create_access_token(email, user_id)
    
    return TokenResponse(
        access_token=access_token,
        user_id=user_id,
        email=email
    )




def get_user_by_token(token: str, db: Session) -> User:
    """Récupère l'utilisateur à partir d'un token JWT"""
    from src.core.security import decode_token
    
    token_data = decode_token(token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    if not user.email_verified:
        raise UserNotVerifiedException()
    
    return user