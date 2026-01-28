from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from src.core.config import settings

# Configuration email
#conf_mail_mailhug = ConnectionConfig(
#    MAIL_FROM=settings.MAIL_FROM,
#    MAIL_PORT=settings.MAIL_PORT,
#    MAIL_SERVER=settings.MAIL_SERVER,
#    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
#)


conf_mail_hypnos = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_HYPNOS_USERNAME,
    MAIL_PASSWORD=settings.MAIL_HYPNOS_PASSWORD,
    MAIL_FROM=settings.MAIL_HYPNOS_FROM,
    MAIL_PORT=settings.MAIL_HYPNOS_PORT,
    MAIL_SERVER=settings.MAIL_HYPNOS_SERVER,
    MAIL_FROM_NAME=settings.MAIL_HYPNOS_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_HYPNOS_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_HYPNOS_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_HYPNOS_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_HYPNOS_VALIDATE_CERTS
)


CONTACT_INFO = """
<p style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; font-size: 13px; color: #666;">
    En cas de problème ou de question, vous pouvez nous contacter sur WhatsApp<br>
</p>
"""

async def send_verification_email(recipient_email: str, code: str) -> bool:
    """
    Envoie un email de vérification avec code à 6 chiffres.
    """
    # Lien de vérification (frontend traitera le code)
    verify_link = f"{settings.FRONTEND_URL}/auth/verify?email={recipient_email}&code={code}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Bienvenue sur Mc'INT!</h2>
        <p>Pour continuer votre réservation, veuillez vérifier votre email.</p>
        
        <p><strong>Votre code de vérification: {code}</strong></p>
        
        <p>Ou cliquez sur le lien ci-dessous:</p>
        <a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Vérifier mon email
        </a>
        
        <p style="color: #999; font-size: 12px;">
            Ce code expire dans 15 minutes.
        </p>
        {CONTACT_INFO}
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"Code MC INT: {code} : Vérification de votre email",
        recipients=[recipient_email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf_mail_hypnos)
    
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        raise Exception(f"Impossible d'envoyer l'email: {str(e)}")


async def send_order_confirmation(user) -> bool:
    """
    Envoie un email de confirmation après paiement avec le 'ticket'.
    """
    from src.print.markdown import generate_markdown_for_one_client
    import markdown2
    
    # Préparation des produits pour le ticket
    produits = []
    if user.menu_item:
        produits.append({"QTE": 1, "PRODUIT": user.menu_item.name, "UNIT": user.menu_item.price, "TOTAL": user.menu_item.price})
    if user.boisson_item:
        produits.append({"QTE": 1, "PRODUIT": user.boisson_item.name, "UNIT": user.boisson_item.price, "TOTAL": user.boisson_item.price})
    if user.bonus_item:
        produits.append({"QTE": 1, "PRODUIT": user.bonus_item.name, "UNIT": user.bonus_item.price, "TOTAL": user.bonus_item.price})

    if user.habite_residence:
        adresse = f"Maisel {user.adresse_if_maisel.value if user.adresse_if_maisel else ''} - Ch {user.numero_if_maisel}"
    else:
        adresse = user.adresse or "Non renseignée"

    ticket_md = generate_markdown_for_one_client(
        Prenom=user.prenom or "Inconnu",
        Nom=user.nom or "Inconnu",
        email=user.email,
        telephone=user.phone or "Non renseigné",
        adresse=adresse,
        horaire=user.heure_reservation.strftime("%Hh%M") if user.heure_reservation else "Non renseigné",
        produits=produits,
        SUM=user.total_amount
    )
    
    ticket_html = markdown2.markdown(ticket_md)
    
    html = f"""
    <html>
    <body style="font-family: 'Courier New', monospace; background-color: #f9f9f9; padding: 20px;">
        <div style="background-color: white; padding: 20px; border: 1px solid #ddd; max-width: 500px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; color: #d32f2f;">MERCI POUR VOTRE COMMANDE !</h2>
            <p>Votre paiement a été confirmé. Voici votre ticket de retrait :</p>
            
            <div style="border: 2px dashed #ccc; padding: 15px; margin: 20px 0; white-space: pre-wrap;">
                {ticket_html}
            </div>
            
            <p style="font-size: 14px; text-align: center; color: #666;">
                Présentez cet email lors de votre retrait le 7 février.
            </p>
            {CONTACT_INFO}
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Confirmation de commande Mc'INT 🍟",
        recipients=[user.email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf_mail_hypnos)
    
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Erreur envoi email confirmation: {e}")
        return False


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

    #fm = FastMail(conf_mail_mailhug)
    fm = FastMail(conf_mail_hypnos)

    try:
        await fm.send_message(message)
    except Exception:
        return False
    return True
