from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from src.core.config import settings

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

# Couleurs du design Mc'INT
COLORS = {
    "red": "#DA291C",
    "red_dark": "#b71c1c",
    "yellow": "#FFC72C",
    "yellow_light": "#FFD54F",
    "dark": "#1a1a1a",
    "dark_light": "#2d2d2d",
    "green": "#10b981",
    "green_dark": "#059669",
    "blue": "#2196F3",
    "orange": "#FF9800",
    "gray": "#666",
    "gray_light": "#f8f8f8",
    "white": "#ffffff",
}

def get_email_wrapper(content: str) -> str:
    """Wrapper HTML pour tous les emails avec le style ticket Mc'INT."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(145deg, {COLORS['dark']} 0%, {COLORS['dark_light']} 50%, {COLORS['dark']} 100%); min-height: 100vh;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-height: 100vh;">
            <tr>
                <td align="center" style="padding: 24px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 480px;">
                        <!-- Ticket perforé haut -->
                        <tr>
                            <td style="height: 16px; background-color: {COLORS['white']}; border-radius: 16px 16px 0 0;"></td>
                        </tr>
                        <!-- Contenu principal -->
                        <tr>
                            <td style="background-color: {COLORS['white']}; padding: 32px;">
                                {content}
                            </td>
                        </tr>
                        <!-- Ticket perforé bas -->
                        <tr>
                            <td style="height: 16px; background-color: {COLORS['white']}; border-radius: 0 0 16px 16px;"></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_email_header(show_badge: bool = False, badge_text: str = "Confirmé") -> str:
    """En-tête avec logo Mc'INT et badge optionnel."""
    badge_html = ""
    if show_badge:
        badge_html = f"""
        <td align="right" valign="middle">
            <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                    <td style="background: linear-gradient(135deg, {COLORS['green']}, {COLORS['green_dark']}); color: {COLORS['white']}; padding: 8px 14px; border-radius: 24px; font-size: 13px; font-weight: 600;">
                        ✓ {badge_text}
                    </td>
                </tr>
            </table>
        </td>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
        <tr>
            <td valign="middle">
                <table role="presentation" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="width: 48px; height: 48px; background: linear-gradient(135deg, {COLORS['red']}, {COLORS['red_dark']}); border-radius: 12px; text-align: center; vertical-align: middle;">
                            <span style="color: {COLORS['yellow']}; font-size: 28px; font-weight: 800; font-family: 'Arial Black', Arial, sans-serif;">M</span>
                        </td>
                        <td style="padding-left: 12px;">
                            <div style="font-size: 24px; font-weight: 800; color: {COLORS['dark']}; line-height: 1;">Mc'INT</div>
                            <div style="font-size: 12px; color: {COLORS['gray']}; font-weight: 500;">by Hypnos</div>
                        </td>
                    </tr>
                </table>
            </td>
            {badge_html}
        </tr>
    </table>
    """

def get_time_section(time_str: str, date_str: str = "7 février 2026") -> str:
    """Section créneau de livraison avec style jaune."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
        <tr>
            <td style="background: linear-gradient(135deg, {COLORS['yellow']} 0%, {COLORS['yellow_light']} 100%); border-radius: 16px; padding: 24px; text-align: center;">
                <div style="font-size: 11px; font-weight: 600; color: rgba(0,0,0,0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Créneau de livraison</div>
                <div style="font-size: 48px; font-weight: 800; color: {COLORS['dark']}; font-family: 'Arial Black', Arial, sans-serif; letter-spacing: 2px;">{time_str}</div>
                <div style="font-size: 14px; font-weight: 600; color: rgba(0,0,0,0.7); margin-top: 8px;">{date_str}</div>
            </td>
        </tr>
    </table>
    """

def get_section_title(icon: str, title: str) -> str:
    """Titre de section avec icône."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 16px;">
        <tr>
            <td style="font-size: 13px; font-weight: 700; color: {COLORS['dark']}; text-transform: uppercase; letter-spacing: 0.5px;">
                <span style="color: {COLORS['red']};">{icon}</span> {title}
            </td>
        </tr>
    </table>
    """

def get_order_item(name: str, item_type: str, price: float) -> str:
    """Ligne de produit avec badge coloré."""
    type_colors = {
        "menu": (COLORS['red'], "Menu"),
        "boisson": (COLORS['blue'], "Boisson"),
        "bonus": (COLORS['orange'], "Extra"),
    }
    color, badge_text = type_colors.get(item_type, (COLORS['gray'], item_type))

    return f"""
    <tr>
        <td style="padding: 14px 16px; background: {COLORS['gray_light']}; border-radius: 12px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                    <td width="28" valign="middle">
                        <div style="width: 28px; height: 28px; background: {color}; border-radius: 50%; text-align: center; line-height: 28px; color: white; font-size: 14px;">✓</div>
                    </td>
                    <td style="padding-left: 12px;" valign="middle">
                        <span style="font-weight: 600; color: {COLORS['dark']}; font-size: 15px;">{name}</span>
                    </td>
                    <td align="right" valign="middle">
                        <span style="font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; background: rgba(0,0,0,0.05); color: {color};">{badge_text}</span>
                    </td>
                    <td width="70" align="right" valign="middle">
                        <span style="font-weight: 600; color: {COLORS['dark']};">{price:.2f} €</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr><td height="10"></td></tr>
    """

def get_total_section(total: float) -> str:
    """Section total avec style sombre."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
        <tr>
            <td style="background: linear-gradient(135deg, {COLORS['dark']}, {COLORS['dark_light']}); border-radius: 12px; padding: 18px 20px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="color: rgba(255,255,255,0.8); font-size: 15px; font-weight: 500;">Total payé</td>
                        <td align="right" style="color: {COLORS['yellow']}; font-size: 28px; font-weight: 800;">{total:.2f} €</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """

def get_separator() -> str:
    """Séparateur en pointillés."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 20px 0;">
        <tr>
            <td style="border-top: 2px dashed #ddd;"></td>
        </tr>
    </table>
    """

def get_info_item(label: str, value: str, full_width: bool = False) -> str:
    """Item d'information dans la grille."""
    width = "100%" if full_width else "48%"
    return f"""
    <td width="{width}" style="background: {COLORS['gray_light']}; padding: 12px 14px; border-radius: 10px; vertical-align: top;">
        <div style="font-size: 10px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div>
        <div style="font-size: 14px; font-weight: 600; color: {COLORS['dark']}; word-break: break-word;">{value}</div>
    </td>
    """

def get_button(text: str, url: str, icon: str = "") -> str:
    """Bouton d'action principal."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 24px;">
        <tr>
            <td align="center">
                <a href="{url}" style="display: inline-block; background: linear-gradient(135deg, {COLORS['red']}, {COLORS['red_dark']}); color: {COLORS['white']}; padding: 16px 32px; border-radius: 12px; font-size: 16px; font-weight: 700; text-decoration: none;">
                    {icon} {text}
                </a>
            </td>
        </tr>
    </table>
    """

def get_contact_section() -> str:
    """Section contacts des responsables."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 24px; background: #e3f2fd; border-radius: 12px; padding: 20px;">
        <tr>
            <td>
                {get_section_title("📞", "Contacts des responsables")}
                <div style="font-size: 13px; color: {COLORS['gray']}; margin-bottom: 12px;">En cas de question concernant votre commande :</div>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td width="50%" style="padding-right: 10px; vertical-align: top;">
                            <div style="font-weight: 600; color: {COLORS['dark']}; font-size: 13px;">Théo DARVOUX</div>
                            <a href="tel:+33762357719" style="color: {COLORS['blue']}; font-size: 11px; text-decoration: none;">+33762357719</a>
                        </td>
                        <td width="50%" style="padding-left: 10px; vertical-align: top;">
                            <div style="font-weight: 600; color: {COLORS['dark']}; font-size: 13px;">Solène CHAMPION</div>
                            <a href="tel:+33661737785" style="color: {COLORS['blue']}; font-size: 11px; text-decoration: none;">+33661737785</a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """

def get_footer() -> str:
    """Pied de page."""
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 24px;">
        <tr>
            <td style="text-align: center; color: #999; font-size: 11px; border-top: 1px solid #eee; padding-top: 16px;">
                <div style="margin-bottom: 8px;">En cas de problème, contactez-nous sur WhatsApp</div>
                <div>Cet email a été envoyé automatiquement.</div>
            </td>
        </tr>
    </table>
    """

async def send_verification_email(recipient_email: str, code: str) -> bool:
    """
    Envoie un email de vérification avec code à 6 chiffres.
    """
    content = f"""
    {get_email_header()}

    <!-- Titre de bienvenue -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px; text-align: center;">
        <tr>
            <td>
                <div style="font-size: 24px; font-weight: 700; color: {COLORS['dark']}; margin-bottom: 8px;">Bienvenue !</div>
                <div style="font-size: 14px; color: {COLORS['gray']};">Pour continuer ta réservation, entre ce code :</div>
            </td>
        </tr>
    </table>

    <!-- Code de vérification -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
        <tr>
            <td style="background: linear-gradient(135deg, {COLORS['yellow']} 0%, {COLORS['yellow_light']} 100%); border-radius: 16px; padding: 32px; text-align: center;">
                <div style="font-size: 11px; font-weight: 600; color: rgba(0,0,0,0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">Ton code de vérification</div>
                <div style="font-size: 48px; font-weight: 800; color: {COLORS['dark']}; font-family: 'Courier New', monospace; letter-spacing: 8px;">{code}</div>
            </td>
        </tr>
    </table>

    <!-- Note expiration -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
        <tr>
            <td style="background: {COLORS['gray_light']}; border-radius: 10px; padding: 14px 16px; text-align: center;">
                <span style="font-size: 12px; color: {COLORS['gray']};">⏱️ Ce code expire dans <strong>15 minutes</strong></span>
            </td>
        </tr>
    </table>

    {get_footer()}
    """

    html = get_email_wrapper(content)

    message = MessageSchema(
        subject=f"🔐 Code Mc'INT : {code}",
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
    import secrets

    # Générer un token de statut s'il n'existe pas
    if not user.status_token:
        user.status_token = secrets.token_urlsafe(32)

    # Helper to resolve item name/price
    from src.menu.utils import load_menu_data
    menu_data = load_menu_data()

    def get_item_details(item_id):
        if not item_id:
            return None
        for cat in ["menus", "boissons", "extras"]:
            for item in menu_data.get(cat, []):
                if item["id"] == item_id:
                    return item
        return None

    menu_details = get_item_details(user.menu_id)
    boisson_details = get_item_details(user.boisson_id)

    # Récupérer tous les extras
    extras_details = []
    if user.bonus_ids:
        for bonus_id in user.bonus_ids:
            details = get_item_details(bonus_id)
            if details:
                extras_details.append(details)

    print(f"[DEBUG] send_order_confirmation: user={user.id}, email={user.email}, total_amount={user.total_amount}")

    if user.habite_residence:
        adresse = f"Maisel {user.adresse_if_maisel.value if user.adresse_if_maisel else ''} - Ch {user.numero_if_maisel}"
    else:
        adresse = user.adresse or "Non renseignée"

    # Lien vers la page de statut
    status_url = f"{settings.FRONTEND_URL}/order/status/{user.status_token}"

    # Formater le créneau horaire (début - fin)
    if user.heure_reservation:
        start_hour = user.heure_reservation.hour
        start_min = user.heure_reservation.minute
        end_hour = start_hour + 1
        time_str = f"{start_hour}h{start_min:02d} - {end_hour}h{start_min:02d}"
    else:
        time_str = "--:-- - --:--"

    # Construire les lignes de produits
    order_items_html = ""
    if menu_details:
        order_items_html += get_order_item(menu_details["name"], "menu", menu_details.get("price", 0))
    if boisson_details:
        order_items_html += get_order_item(boisson_details["name"], "boisson", boisson_details.get("price", 0))
    for extra in extras_details:
        order_items_html += get_order_item(extra["name"], "bonus", extra.get("price", 0))

    # Notes spéciales si présentes
    special_notes_html = ""
    if user.special_requests:
        special_notes_html = f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 12px;">
            <tr>
                <td style="background: #fff3e0; border-left: 4px solid {COLORS['orange']}; padding: 12px 14px; border-radius: 0 10px 10px 0;">
                    <div style="font-size: 10px; font-weight: 600; color: {COLORS['orange']}; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Notes</div>
                    <div style="font-size: 13px; color: {COLORS['dark']};">{user.special_requests}</div>
                </td>
            </tr>
        </table>
        """

    content = f"""
    {get_email_header(show_badge=True, badge_text="Confirmé")}

    <!-- Message de remerciement -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px; text-align: center;">
        <tr>
            <td>
                <div style="font-size: 22px; font-weight: 700; color: {COLORS['dark']};">Merci pour ta commande !</div>
            </td>
        </tr>
    </table>

    {get_time_section(time_str)}

    <!-- Section commande -->
    {get_section_title("🛒", "Ta commande")}
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 20px;">
        {order_items_html}
    </table>

    {get_total_section(user.total_amount or 0)}

    {get_separator()}

    <!-- Section informations -->
    {get_section_title("👤", "Informations")}
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 20px;">
        <tr>
            {get_info_item("Nom", f"{user.prenom or ''} {user.nom or ''}")}
            <td width="4%"></td>
            {get_info_item("Téléphone", user.phone or "Non renseigné")}
        </tr>
        <tr><td colspan="3" height="12"></td></tr>
        <tr>
            <td colspan="3" style="background: {COLORS['gray_light']}; padding: 12px 14px; border-radius: 10px;">
                <div style="font-size: 10px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Adresse de livraison</div>
                <div style="font-size: 14px; font-weight: 600; color: {COLORS['dark']};">{adresse}</div>
            </td>
        </tr>
    </table>

    {special_notes_html}

    {get_separator()}

    <!-- Bouton suivi -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="text-align: center;">
        <tr>
            <td>
                <a href="{status_url}" style="display: inline-block; background: linear-gradient(135deg, {COLORS['green']}, {COLORS['green_dark']}); color: {COLORS['white']}; padding: 16px 32px; border-radius: 12px; font-size: 15px; font-weight: 700; text-decoration: none;">
                    📊 Suivre ma commande
                </a>
                <div style="font-size: 11px; color: {COLORS['gray']}; margin-top: 12px;">Conserve ce lien pour consulter le statut à tout moment</div>
            </td>
        </tr>
    </table>

    {get_contact_section()}

    {get_footer()}
    """

    html = get_email_wrapper(content)

    message = MessageSchema(
        subject="✅ Commande Mc'INT confirmée - 7 février 2026",
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
    content = f"""
    {get_email_header()}

    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="text-align: center;">
        <tr>
            <td>
                <div style="font-size: 24px; font-weight: 700; color: {COLORS['dark']}; margin-bottom: 16px;">Email de test</div>
                <div style="font-size: 14px; color: {COLORS['gray']};">Si tu vois ce message, la configuration email fonctionne correctement !</div>
            </td>
        </tr>
    </table>

    {get_footer()}
    """

    html = get_email_wrapper(content)

    message = MessageSchema(
        subject="🧪 Test Mc'INT",
        recipients=[recipient_email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf_mail_hypnos)

    try:
        await fm.send_message(message)
    except Exception:
        return False
    return True
