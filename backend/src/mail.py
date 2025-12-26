
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

conf_mail_dev = ConnectionConfig(
    MAIL_USERNAME = "username",
    MAIL_PASSWORD = "password",
    MAIL_FROM = "test@example.com",
    MAIL_PORT = 1025,
    MAIL_SERVER = "mail",
    MAIL_FROM_NAME="Test Email",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = False,
    VALIDATE_CERTS = False
)

conf = conf_mail_dev#A enlever quand plus en dev
# pas tres propre a refaire en mettant dans un env variable????? 
# TODO

async def send_test_email(recipient_email: str) -> bool:
    """
    Fonction interne pour envoyer un email de test
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

    fm = FastMail(conf)

    try:
        await fm.send_message(message)
    except Exception:
        return False
    return True
