from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Configuration application utilisant les variables d'environnement
    """
    # Base de données
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60  # Token d'accès expire en 24 heures
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh token expire en 7 jours
    
    # Code de vérification email
    EMAIL_CODE_EXPIRE_MINUTES: int = 60  # Code email expire en 60 minutes
    EMAIL_CODE_LENGTH: int = 4  # Longueur du code (4 chiffres)
    
    # BDE API
    BDE_API_URL: str = os.getenv("BDE_API_URL")
    BDE_API_KEY: str = os.getenv("BDE_API_KEY")  # À définir en env
    BDE_API_TIMEOUT: int = int(os.getenv("BDE_API_TIMEOUT", "5"))  # Timeout en secondes
    
    # Email (FastMail)
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "username")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "password")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "test@example.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "MC INT")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "mail")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "false").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "false").lower() == "true"
    MAIL_USE_CREDENTIALS: bool = os.getenv("MAIL_USE_CREDENTIALS", "false").lower() == "true"
    MAIL_VALIDATE_CERTS: bool = os.getenv("MAIL_VALIDATE_CERTS", "false").lower() == "true"
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    
    # HelloAsso (OAuth2)
    HELLOASSO_CLIENT_ID: str = os.getenv("HELLOASSO_CLIENT_ID", "")
    HELLOASSO_CLIENT_SECRET: str = os.getenv("HELLOASSO_CLIENT_SECRET", "")
    HELLOASSO_URL_TOKEN: str = os.getenv("HELLOASSO_URL_TOKEN", "https://api.helloasso.com/oauth2")
    HELLOASSO_API: str = os.getenv("HELLOASSO_API", "https://api.helloasso.com/v5")
    HELLOASSO_ORGANIZATION_SLUG: str = os.getenv("HELLOASSO_ORGANIZATION_SLUG", "")
    # HTTPS URL for HelloAsso redirects (required by HelloAsso)
    HELLOASSO_REDIRECT_BASE_URL: str = os.getenv("HELLOASSO_REDIRECT_BASE_URL", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
