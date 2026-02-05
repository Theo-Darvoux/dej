"""
Module de génération des bons de commande PDF style ticket de caisse.
Design moderne et professionnel.
"""
from typing import List, Dict, Any
from fpdf import FPDF
from io import BytesIO
import os


# Dimensions des tickets (en mm)
TICKET_WIDTH = 95
TICKET_HEIGHT_MIN = 65  # Minimum height
TICKET_HEIGHT_BASE = 50  # Base height without products
PRODUCT_HEIGHT = 5  # Height per product line
MARGIN = 5
TICKETS_PER_ROW = 2
PAGE_HEIGHT = 297  # A4 height


def _sanitize_text_for_pdf(text: str) -> str:
    """
    Sanitize text for FPDF by replacing Unicode characters with ASCII equivalents.

    FPDF's core fonts (Helvetica, Times, etc.) only support Latin-1 encoding.
    This function replaces common Unicode characters with ASCII equivalents.
    """
    if not text:
        return text

    # Mapping of Unicode characters to ASCII equivalents
    replacements = {
        # Smart quotes
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201C': '"',  # Left double quotation mark
        '\u201D': '"',  # Right double quotation mark
        # Dashes
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2015': '--', # Horizontal bar
        # Spaces
        '\u00A0': ' ',  # Non-breaking space
        '\u2009': ' ',  # Thin space
        '\u200A': ' ',  # Hair space
        # Other common characters
        '\u2026': '...', # Horizontal ellipsis
        '\u2022': '*',   # Bullet
        '\u00B0': 'deg', # Degree sign
    }

    # Replace Unicode characters
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)

    # Remove any remaining non-Latin-1 characters
    # Replace with '?' or remove them
    try:
        text.encode('latin-1')
    except UnicodeEncodeError:
        # Replace any remaining problematic characters
        text = text.encode('latin-1', errors='replace').decode('latin-1')

    return text


def _calculate_ticket_height(num_products: int, has_email: bool, has_phone: bool, special_requests_lines: int) -> float:
    """Calculate dynamic ticket height based on content."""
    # Base: header(12) + time_banner(8) + name(5) + address(4) + separator(5) + footer(10) + padding(6)
    height = TICKET_HEIGHT_BASE

    if has_email:
        height += 3.5
    if has_phone:
        height += 3
    if special_requests_lines > 0:
        # 1 line for "Note:" label + (3mm per line of text) + 1mm padding
        height += 1 + (special_requests_lines * 3) + 1

    # Add space for each product
    height += num_products * PRODUCT_HEIGHT

    return max(height, TICKET_HEIGHT_MIN)


def _calculate_special_requests_lines(text: str, max_lines: int = 6, max_chars_per_line: int = 45) -> int:
    """Calculate how many lines the special requests will take (max 6 lines)."""
    if not text:
        return 0
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                if len(lines) >= max_lines:
                    break
            current_line = word
    
    if current_line and len(lines) < max_lines:
        lines.append(current_line)
    
    return min(len(lines), max_lines)


class TicketPDF(FPDF):
    """PDF customisé pour les tickets."""
    pass


def generate_pdf_for_all_clients(reservations: List[Any]) -> bytes:
    """Génère un PDF avec tickets de taille dynamique (2 colonnes)."""
    pdf = TicketPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)

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

    # Track Y position for each column
    col_y = [MARGIN, MARGIN]  # [left_col_y, right_col_y]
    current_page = 0

    for user in reservations:
        # Préparation des produits
        menu_details = get_item_details(user.menu_id)
        boisson_details = get_item_details(user.boisson_id)

        produits = []
        if menu_details:
            produits.append({
                "nom": menu_details["name"],
                "prix": menu_details.get("price", 0),
                "type": "menu"
            })
        if boisson_details:
            produits.append({
                "nom": boisson_details["name"],
                "prix": boisson_details.get("price", 0),
                "type": "boisson"
            })
        # Ajouter tous les extras
        if user.bonus_ids:
            for bonus_id in user.bonus_ids:
                bonus_details = get_item_details(bonus_id)
                if bonus_details:
                    produits.append({
                        "nom": bonus_details["name"],
                        "prix": bonus_details.get("price", 0),
                        "type": "extra"
                    })

        # Adresse / Logement
        if user.habite_residence:
            batiment = user.adresse_if_maisel.value if user.adresse_if_maisel else ''
            adresse = f"Maisel {batiment}"
            chambre = str(user.numero_if_maisel) if user.numero_if_maisel else ""
        else:
            adresse = user.adresse or "Non renseignée"
            chambre = ""

        # Calculate number of special request lines (max 6)
        special_requests_lines = 0
        if user.special_requests and user.special_requests.strip():
            special_requests_lines = _calculate_special_requests_lines(
                user.special_requests.strip(), max_lines=6, max_chars_per_line=45
            )
        
        # Calculate dynamic ticket height
        ticket_height = _calculate_ticket_height(
            num_products=len(produits),
            has_email=bool(user.email),
            has_phone=bool(user.phone),
            special_requests_lines=special_requests_lines
        )

        # Choose column with less height (balances columns)
        col = 0 if col_y[0] <= col_y[1] else 1

        # Check if ticket fits on current page
        if col_y[col] + ticket_height > PAGE_HEIGHT - MARGIN:
            # Try other column
            other_col = 1 - col
            if col_y[other_col] + ticket_height <= PAGE_HEIGHT - MARGIN:
                col = other_col
            else:
                # Both columns full, new page
                pdf.add_page()
                current_page += 1
                col_y = [MARGIN, MARGIN]
                col = 0

        # First page needs to be added
        if current_page == 0 and col_y[0] == MARGIN and col_y[1] == MARGIN:
            pdf.add_page()
            current_page = 1

        # Calculate X position
        x = MARGIN + col * (TICKET_WIDTH + MARGIN)
        y = col_y[col]

        # Dessiner le ticket
        _draw_beautiful_ticket(
            pdf=pdf,
            x=x,
            y=y,
            ticket_height=ticket_height,
            numero_commande=user.id,
            prenom=user.prenom or "",
            nom=user.nom or "",
            email=user.email or "",
            telephone=user.phone or "",
            adresse=adresse,
            chambre=chambre,
            horaire=user.heure_reservation.strftime("%H:%M") if user.heure_reservation else "?",
            produits=produits,
            total=user.total_amount or 0,
            special_requests=user.special_requests,
            is_maisel=user.habite_residence
        )

        # Update column Y position
        col_y[col] += ticket_height + MARGIN

    return bytes(pdf.output())


def _draw_beautiful_ticket(
    pdf: FPDF,
    x: float,
    y: float,
    ticket_height: float,
    numero_commande: int,
    prenom: str,
    nom: str,
    email: str,
    telephone: str,
    adresse: str,
    chambre: str,
    horaire: str,
    produits: List[Dict[str, Any]],
    total: float,
    special_requests: str = None,
    is_maisel: bool = False
):
    """Dessine un ticket de caisse élégant avec hauteur dynamique."""

    # === CADRE PRINCIPAL ===
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.4)
    pdf.rect(x, y, TICKET_WIDTH, ticket_height)

    # === EN-TÊTE AVEC FOND ===
    pdf.set_fill_color(45, 45, 45)
    pdf.rect(x, y, TICKET_WIDTH, 12, 'F')

    # Logo / Titre
    pdf.set_xy(x, y + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(TICKET_WIDTH, 4, "Mc'INT", align="C")

    # Sous-titre
    pdf.set_xy(x, y + 6)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(TICKET_WIDTH, 3, "by Hypnos", align="C")

    # Reset text color
    pdf.set_text_color(0, 0, 0)

    # === BANDEAU HORAIRE ===
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(x, y + 12, TICKET_WIDTH, 8, 'F')

    # Numéro commande à gauche
    pdf.set_xy(x + 3, y + 13.5)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(30, 5, f"#{numero_commande:04d}", align="L")

    # Horaire au centre (gros)
    pdf.set_xy(x + 30, y + 13)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(TICKET_WIDTH - 60, 6, horaire, align="C")

    # Indicateur Maisel/Externe à droite
    pdf.set_xy(x + TICKET_WIDTH - 25, y + 13.5)
    pdf.set_font("Helvetica", "B", 6)
    if is_maisel:
        pdf.set_text_color(0, 100, 180)
        pdf.cell(22, 5, "MAISEL", align="R")
    else:
        pdf.set_text_color(180, 100, 0)
        pdf.cell(22, 5, "EXTERNE", align="R")

    pdf.set_text_color(0, 0, 0)

    # === INFOS CLIENT ===
    current_y = y + 22

    # Nom du client (en gras, bien visible)
    pdf.set_xy(x + 3, current_y)
    pdf.set_font("Helvetica", "B", 10)
    nom_complet = f"{prenom} {nom}".strip()
    if len(nom_complet) > 25:
        nom_complet = nom_complet[:24] + "."
    pdf.cell(TICKET_WIDTH - 6, 5, _sanitize_text_for_pdf(nom_complet), align="L")
    current_y += 5

    # Email
    if email:
        pdf.set_xy(x + 3, current_y)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(100, 100, 100)
        email_display = email if len(email) <= 35 else email[:34] + "."
        pdf.cell(TICKET_WIDTH - 6, 3, _sanitize_text_for_pdf(email_display), align="L")
        current_y += 3.5

    # Adresse et chambre
    pdf.set_xy(x + 3, current_y)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(80, 80, 80)

    if is_maisel and chambre:
        info_lieu = f"{adresse} - Chambre {chambre}"
    else:
        info_lieu = adresse

    if len(info_lieu) > 40:
        info_lieu = info_lieu[:39] + "."
    pdf.cell(TICKET_WIDTH - 6, 4, _sanitize_text_for_pdf(info_lieu), align="L")
    current_y += 4

    # Téléphone
    if telephone:
        pdf.set_xy(x + 3, current_y)
        pdf.set_font("Helvetica", "", 6)
        pdf.cell(TICKET_WIDTH - 6, 3, _sanitize_text_for_pdf(f"Tel: {telephone}"), align="L")
        current_y += 3

    pdf.set_text_color(0, 0, 0)

    # === LIGNE SÉPARATRICE POINTILLÉE ===
    current_y += 2
    pdf.set_draw_color(150, 150, 150)
    pdf.set_line_width(0.2)
    _draw_dashed_line(pdf, x + 3, current_y, x + TICKET_WIDTH - 3, current_y)
    current_y += 3

    # === PRODUITS ===
    pdf.set_font("Helvetica", "", 8)

    for p in produits:
        pdf.set_xy(x + 3, current_y)

        # Icône selon le type
        if p["type"] == "menu":
            icon = ">"
        else:
            icon = "+"

        # Nom du produit
        nom_produit = p["nom"]
        if len(nom_produit) > 22:
            nom_produit = nom_produit[:21] + "."

        pdf.set_font("Helvetica", "", 8)
        pdf.cell(5, 4, icon, align="L")
        pdf.cell(55, 4, _sanitize_text_for_pdf(nom_produit), align="L")

        # Prix
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(TICKET_WIDTH - 66, 4, f"{p['prix']:.2f} E", align="R")

        current_y += 5

    # === DEMANDES SPÉCIALES ===
    if special_requests and special_requests.strip():
        current_y += 1
        pdf.set_xy(x + 3, current_y)
        pdf.set_font("Helvetica", "I", 6)
        pdf.set_text_color(100, 100, 100)
        
        # Split text into lines (max 6 lines, ~45 chars per line)
        note = special_requests.strip()
        max_lines = 6
        max_chars_per_line = 45
        
        words = note.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    if len(lines) >= max_lines:
                        break
                current_line = word
        
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        # Add "..." if text was truncated
        remaining_text = " ".join(words[len(" ".join(lines).split()):])
        if remaining_text.strip():
            if lines:
                lines[-1] = lines[-1].rstrip() + "..."
            else:
                lines = [note[:max_chars_per_line-3] + "..."]
        
        # Render "Note:" label
        pdf.cell(TICKET_WIDTH - 6, 3, "Note:", align="L")
        current_y += 3
        
        # Render each line
        for line in lines:
            pdf.set_xy(x + 5, current_y)
            pdf.cell(TICKET_WIDTH - 8, 3, _sanitize_text_for_pdf(line), align="L")
            current_y += 3
        
        pdf.set_text_color(0, 0, 0)
        current_y -= 3  # Adjust back since we incremented in the loop

    # === TOTAL ===
    pdf.set_fill_color(45, 45, 45)
    pdf.rect(x, y + ticket_height - 10, TICKET_WIDTH, 10, 'F')

    pdf.set_xy(x + 3, y + ticket_height - 8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(TICKET_WIDTH - 6, 6, f"TOTAL: {total:.2f} EUR", align="R")

    pdf.set_text_color(0, 0, 0)


def _draw_dashed_line(pdf: FPDF, x1: float, y1: float, x2: float, y2: float, dash_length: float = 1.5, gap: float = 1):
    """Dessine une ligne pointillée."""
    total_length = x2 - x1
    current_x = x1

    while current_x < x2:
        end_x = min(current_x + dash_length, x2)
        pdf.line(current_x, y1, end_x, y2)
        current_x = end_x + gap


def generate_markdown_for_one_client(
    Prenom: str,
    Nom: str,
    email: str,
    telephone: str,
    adresse: str,
    horaire: str,
    produits: List[Dict[str, Any]],
    SUM: float
) -> str:
    """Fonction dépréciée - gardée pour compatibilité."""
    produits_lines = "\n    ".join(
        f"{p['QTE']:<3} {p['PRODUIT']:<14} {p['UNIT']:>4.2f} E {p['TOTAL']:>4.2f} E"
        for p in produits
    )

    return f"""
    Restaurant Mc'INT by Hypnos
    -------------------------------
    {Prenom} {Nom}
    Horaire: {horaire} | Tel: {telephone}
    Adresse: {adresse}
    -------------------------------
    {produits_lines}
    Total: {SUM:.2f} E
    """


if __name__ == "__main__":
    # Test simple
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=12)
    pdf.cell(0, 10, "Test PDF - Mc'INT", ln=True, align="C")

    output_path = os.path.join(os.path.dirname(__file__), "output.pdf")
    pdf.output(output_path)
    print(f"PDF genere: {output_path}")
