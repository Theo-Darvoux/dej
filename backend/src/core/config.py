from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Configuration application utilisant les variables d'environnement
    """
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    # Base de données
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # Token d'accès expire en 2 heures (for long checkout flows)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Token de rafraîchissement expire en 7 jours
    
    # Code de vérification email
    EMAIL_CODE_EXPIRE_MINUTES: int = 15  # Code email expire en 60 minutes
    EMAIL_CODE_LENGTH: int = 6  # Longueur du code (6 caractères)
    
    # BDE API
    BDE_API_URL: str = os.getenv("BDE_API_URL")
    BDE_API_KEY: str = os.getenv("BDE_API_KEY")  # À définir en env
    BDE_API_TIMEOUT: int = int(os.getenv("BDE_API_TIMEOUT", "5"))  # Timeout en secondes
    
    # Email (FastMail)
    MAIL_FROM: str = os.getenv("MAIL_FROM", "test@example.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "MC INT")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "mail")
    
    # Email (FastMail)
    MAIL_HYPNOS_USERNAME: str = os.getenv("MAIL_HYPNOS_USERNAME", "username")
    MAIL_HYPNOS_PASSWORD: str = os.getenv("MAIL_HYPNOS_PASSWORD", "password")
    MAIL_HYPNOS_FROM: str = os.getenv("MAIL_HYPNOS_FROM", "test@example.com")
    MAIL_HYPNOS_FROM_NAME: str = os.getenv("MAIL_HYPNOS_FROM_NAME", "MC INT")
    MAIL_HYPNOS_PORT: int = int(os.getenv("MAIL_HYPNOS_PORT", "1025"))
    MAIL_HYPNOS_SERVER: str = os.getenv("MAIL_HYPNOS_SERVER", "mail")
    MAIL_HYPNOS_STARTTLS: bool = os.getenv("MAIL_HYPNOS_STARTTLS", "false").lower() == "true"
    MAIL_HYPNOS_SSL_TLS: bool = os.getenv("MAIL_HYPNOS_SSL_TLS", "false").lower() == "true"
    MAIL_HYPNOS_USE_CREDENTIALS: bool = os.getenv("MAIL_HYPNOS_USE_CREDENTIALS", "false").lower() == "true"
    MAIL_HYPNOS_VALIDATE_CERTS: bool = os.getenv("MAIL_HYPNOS_VALIDATE_CERTS", "false").lower() == "true"
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    HELLOASSO_REDIRECT_BASE_URL: str = os.getenv("HELLOASSO_REDIRECT_BASE_URL")
    HELLOASSO_ORGANIZATION_SLUG: str = os.getenv("HELLOASSO_ORGANIZATION_SLUG")
    
    # HelloAsso (OAuth2)
    HELLOASSO_CLIENT_ID: str = os.getenv("HELLOASSO_CLIENT_ID", "")
    HELLOASSO_CLIENT_SECRET: str = os.getenv("HELLOASSO_CLIENT_SECRET", "")
    HELLOASSO_ITEM_NAME: str = os.getenv("HELLOASSO_ITEM_NAME", "Petit-Déjeuner HYPNOS")

    HELLOASSO_URL_TOKEN: str = os.getenv("HELLOASSO_URL_TOKEN", "https://api.helloasso.com/oauth2")
    HELLOASSO_API: str = os.getenv("HELLOASSO_API", "https://api.helloasso.com/v5")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
