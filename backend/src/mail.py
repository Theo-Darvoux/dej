from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from src.core.config import settings

# Configuration email
conf_mail = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS
)


async def send_verification_email(recipient_email: str, code: str) -> bool:
    """
    Envoie un email de vérification avec code à 6 chiffres.
    """
    # Lien de vérification (frontend traitera le code)
    verify_link = f"{settings.FRONTEND_URL}/auth/verify?email={recipient_email}&code={code}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Bienvenue sur MC INT!</h2>
        <p>Pour continuer votre réservation, veuillez vérifier votre email.</p>
        
        <p><strong>Votre code de vérification: {code}</strong></p>
        
        <p>Ou cliquez sur le lien ci-dessous:</p>
        <a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Vérifier mon email
        </a>
        
        <p style="color: #999; font-size: 12px;">
            Ce code expire dans 15 minutes.
        </p>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"Code MC INT: {code} : Vérification de votre email",
        recipients=[recipient_email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf_mail)
    
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        raise Exception(f"Impossible d'envoyer l'email: {str(e)}")


async def send_test_email(recipient_email: str) -> bool:
    """
    Fonction interne pour envoyer un email de test a l'adresse donnée en paramètre.
    """
    html = f"""
    <p>Mail de test !</p>
    <p>Merci d'utiliser notre service !</p>
    """

    message = MessageSchema(
        subject="Test d'email",
        recipients=[recipient_email],
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf_mail)

    try:
        await fm.send_message(message)
    except Exception:
        return False
    return True
