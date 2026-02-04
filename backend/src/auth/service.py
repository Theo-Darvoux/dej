import random
import string
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

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


def is_user_blacklisted(identity: str) -> bool:
    """
    Vérifie si l'utilisateur (prenom.nom) est dans la blacklist.
    Normalise les _ en . pour la comparaison.
    """
    import json
    import os
    
    blacklist_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "blacklist.json")
    
    # Normaliser l'identité (remplacer _ par .)
    normalized_identity = identity.lower().replace("_", ".")
    
    try:
        with open(blacklist_path, "r") as f:
            data = json.load(f)
            blocked_users = data.get("blocked_users", [])
            # Normaliser aussi les entrées de la blacklist
            normalized_blocked = [u.lower().replace("_", ".") for u in blocked_users]
            return normalized_identity in normalized_blocked
    except (FileNotFoundError, json.JSONDecodeError):
        return False


async def request_verification_code(email: str, db: Session) -> bool:
    """
    Génère et envoie un code de vérification par email.
    Retourne True si succès, lance exception sinon.
    """
    # Valider et normaliser l'email
    delivery_email, identity = normalize_email(email)
    
    # Vérifier la blacklist
    if is_user_blacklisted(identity):
        raise InvalidCredentialsException("Vous n'avez pas le droit de commander")
    
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
    except IntegrityError:
        # Race condition: another request created the user between our check and insert
        db.rollback()
        # Retry by fetching the existing user and updating
        user = db.query(User).filter(User.normalized_email == identity).first()
        if not user:
            # Try by email as fallback
            user = db.query(User).filter(User.email == delivery_email).first()
        if not user:
            raise EmailSendFailedException("Erreur base de données")
        user.email = delivery_email
        user.normalized_email = identity  # Sync normalized_email
        user.verification_code = code
        user.code_created_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise EmailSendFailedException("Erreur base de données")
    except Exception:
        db.rollback()
        raise EmailSendFailedException("Erreur base de données")
    
    # Envoyer email (utiliser delivery_email)
    try:
        await send_verification_email(delivery_email, code)
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
    delivery_email, identity = normalize_email(email)

    # Chercher utilisateur par normalized_email (identité unique)
    user = db.query(User).filter(User.normalized_email == identity).first()
    if not user:
        # Fallback: chercher par email
        user = db.query(User).filter(User.email == delivery_email).first()
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    # Vérifier si l'utilisateur a déjà commandé (paiement complété)
    # Exception: admins can always login regardless of order status
    if user.payment_status == "completed" and user.user_type != "admin":
        raise InvalidCredentialsException("Vous avez déjà passé une commande avec cet email. Contactez Solène ou Théo pour toute modification.")
    
    # TODO DEBUT
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

    is_cotisant = await verify_with_bde(email)

    # Extraire prénom/nom depuis l'email (format prenom.nom@...)
    try:
        local_part = email.split("@")[0]
        parts = [p for p in local_part.replace("_", ".").replace("-", ".").split(".") if p]
        if len(parts) >= 2:
            prenom_raw, nom_raw = parts[0], parts[1]
            prenom = prenom_raw.strip().capitalize()
            nom = nom_raw.strip().capitalize()
            # Only set if they're valid (not empty and not just punctuation)
            if prenom and len(prenom) > 1 and prenom.isalpha():
                user.prenom = prenom
            else:
                user.prenom = None
            if nom and len(nom) > 1 and nom.isalpha():
                user.nom = nom
            else:
                user.nom = None
        else:
            user.prenom = None
            user.nom = None
    except Exception:
        user.prenom = None
        user.nom = None

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
    """Génère access et refresh tokens JWT"""
    from src.core.security import create_refresh_token
    
    access_token = create_access_token(email, user_id)
    refresh_token = create_refresh_token(email, user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=email
    )




def get_user_by_token(token: str, db: Session, expected_type: str = "access") -> User:
    """Récupère l'utilisateur à partir d'un token JWT"""
    from src.core.security import decode_token
    
    token_data = decode_token(token, expected_type=expected_type)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if not user:
        raise InvalidCredentialsException("Utilisateur non trouvé")
    
    if not user.email_verified:
        raise UserNotVerifiedException()
    
    return user