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
    Envoie un email de confirmation après paiement avec :
    - Récapitulatif de la commande
    - Bon de livraison
    - Contacts des responsables
    - Lien permanent vers le statut de commande
    """
    from src.print.markdown import generate_markdown_for_one_client
    import markdown2
    import secrets
    
    # Générer un token de statut s'il n'existe pas
    if not user.status_token:
        user.status_token = secrets.token_urlsafe(32)
        # Note: Le commit doit être fait par l'appelant après cette fonction
    
    # Préparation des produits pour le ticket
    produits = []
    if user.menu_item:
        produits.append({"QTE": 1, "PRODUIT": user.menu_item.name, "UNIT": user.menu_item.price, "TOTAL": user.menu_item.price})
    if user.boisson_item:
        produits.append({"QTE": 1, "PRODUIT": user.boisson_item.name, "UNIT": user.boisson_item.price, "TOTAL": user.boisson_item.price})
    if user.bonus_item:
        produits.append({"QTE": 1, "PRODUIT": user.bonus_item.name, "UNIT": user.bonus_item.price, "TOTAL": user.bonus_item.price})

    print(f"[DEBUG] send_order_confirmation: user={user.id}, email={user.email}, products_count={len(produits)}, total_amount={user.total_amount}")

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
    
    # Lien vers la page de statut
    status_url = f"{settings.FRONTEND_URL}/order/status/{user.status_token}"
    
    # Liste des produits commandés
    order_items_html = ""
    for p in produits:
        order_items_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{p['PRODUIT']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{p['TOTAL']:.2f} €</td>
        </tr>
        """
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            
            <!-- En-tête -->
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #d32f2f; margin: 0;">🍔 Mc'INT</h1>
                <h2 style="color: #333; margin-top: 10px;">Merci pour votre commande !</h2>
            </div>
            
            <!-- Récapitulatif -->
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #333;">📋 Récapitulatif de votre commande</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #e0e0e0;">
                            <th style="padding: 10px; text-align: left;">Produit</th>
                            <th style="padding: 10px; text-align: right;">Prix</th>
                        </tr>
                    </thead>
                    <tbody>
                        {order_items_html}
                    </tbody>
                    <tfoot>
                        <tr style="font-weight: bold; background-color: #d32f2f; color: white;">
                            <td style="padding: 10px;">TOTAL</td>
                            <td style="padding: 10px; text-align: right;">{user.total_amount:.2f} €</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
            
            <!-- Infos livraison -->
            <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ff9800;">
                <h3 style="margin-top: 0; color: #e65100;">📍 Informations de livraison</h3>
                <p><strong>Date :</strong> 7 février 2026</p>
                <p><strong>Heure :</strong> {user.heure_reservation.strftime("%Hh%M") if user.heure_reservation else "Non renseigné"}</p>
                <p><strong>Adresse :</strong> {adresse}</p>
                <p><strong>Téléphone :</strong> {user.phone or "Non renseigné"}</p>
                {f'<p><strong>Notes :</strong> {user.special_requests}</p>' if user.special_requests else ''}
            </div>
            
            <!-- Bon de livraison (ticket) -->
            <div style="border: 2px dashed #ccc; padding: 15px; margin: 20px 0; background-color: #fafafa;">
                <h3 style="margin-top: 0; text-align: center;">🎫 Votre bon de livraison</h3>
                <div style="font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 12px;">
                    {ticket_html}
                </div>
                <p style="font-size: 12px; text-align: center; color: #666; margin-bottom: 0;">
                    Présentez cet email lors de votre retrait.
                </p>
            </div>
            
            <!-- Lien statut commande -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{status_url}" style="background-color: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    📊 Suivre ma commande
                </a>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">
                    Conservez ce lien pour consulter le statut de votre commande à tout moment.
                </p>
            </div>
            
            <!-- Contacts responsables -->
            <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h3 style="margin-top: 0; color: #1565c0;">📞 Contacts des responsables</h3>
                <p>En cas de question ou problème concernant votre commande :</p>
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div style="flex: 1; min-width: 200px;">
                        <p><strong>Théo DARVOUX</strong><br>
                        <a href="mailto:theo.darvoux@telecom-sudparis.eu">theo.darvoux@telecom-sudparis.eu</a></p>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <p><strong>Solène CHAMPION</strong><br>
                        <a href="mailto:solene.champion@telecom-sudparis.eu">solene.champion@telecom-sudparis.eu</a></p>
                    </div>
                </div>
            </div>
            
            {CONTACT_INFO}
            
            <p style="text-align: center; color: #999; font-size: 11px; margin-top: 30px;">
                Cet email a été envoyé automatiquement. Merci de ne pas y répondre directement.
            </p>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="✅ Confirmation de commande Mc'INT - 7 février 2026",
        recipients=[user.email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf_mail_hypnos)
    
    try:
        print(f"[DEBUG] Attempting to send message to {user.email}")
        await fm.send_message(message)
        print(f"[DEBUG] Message sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"[ERROR] Erreur envoi email confirmation to {user.email}: {e}")
        import traceback
        traceback.print_exc()
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
