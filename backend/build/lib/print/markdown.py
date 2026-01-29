#on appel la base de donnée pour récupérer les infos de la réservation
#on passe pour toutes les réservations
from typing import List, Dict, Any
from fpdf import FPDF
from io import BytesIO
import os


# Dimensions des petits tickets (en mm)
TICKET_WIDTH = 95  # 2 colonnes sur A4 (210mm)
TICKET_HEIGHT = 70  # ~4 tickets par colonne
MARGIN = 5
TICKETS_PER_ROW = 2
TICKETS_PER_COL = 4


def generate_pdf_for_all_clients(reservations: List[Any]) -> bytes:
    """Génère un PDF avec plusieurs petits tickets par page (grille 2x4)."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    
    ticket_count = 0
    
    for user in reservations:
        # Préparation des produits
        produits = []
        if user.menu_item:
            produits.append({
                "QTE": 1,
                "PRODUIT": user.menu_item.name,
                "UNIT": user.menu_item.price,
                "TOTAL": user.menu_item.price
            })
        if user.boisson_item:
            produits.append({
                "QTE": 1,
                "PRODUIT": user.boisson_item.name,
                "UNIT": user.boisson_item.price,
                "TOTAL": user.boisson_item.price
            })
        if user.bonus_item:
            produits.append({
                "QTE": 1,
                "PRODUIT": user.bonus_item.name,
                "UNIT": user.bonus_item.price,
                "TOTAL": user.bonus_item.price
            })

        # Adresse / Logement
        if user.habite_residence:
            adresse = f"Maisel {user.adresse_if_maisel.value if user.adresse_if_maisel else ''} - Ch {user.numero_if_maisel}"
        else:
            adresse = user.adresse or "Non renseignée"

        # Calculer la position du ticket dans la grille
        tickets_per_page = TICKETS_PER_ROW * TICKETS_PER_COL
        position_on_page = ticket_count % tickets_per_page
        
        # Nouvelle page si nécessaire
        if position_on_page == 0:
            pdf.add_page()
        
        # Calculer X et Y
        col = position_on_page % TICKETS_PER_ROW
        row = position_on_page // TICKETS_PER_ROW
        
        x = MARGIN + col * (TICKET_WIDTH + MARGIN)
        y = MARGIN + row * (TICKET_HEIGHT + MARGIN)
        
        # Dessiner le ticket
        _draw_ticket(
            pdf=pdf,
            x=x,
            y=y,
            prenom=user.prenom or "?",
            nom=user.nom or "?",
            telephone=user.phone or "",
            adresse=adresse,
            horaire=user.heure_reservation.strftime("%Hh%M") if user.heure_reservation else "?",
            produits=produits,
            total=user.total_amount
        )
        
        ticket_count += 1
    
    # Retourner les bytes du PDF
    return bytes(pdf.output())


def _draw_ticket(
    pdf: FPDF,
    x: float,
    y: float,
    prenom: str,
    nom: str,
    telephone: str,
    adresse: str,
    horaire: str,
    produits: List[Dict[str, Any]],
    total: float
):
    """Dessine un petit ticket à la position (x, y)."""
    # Cadre du ticket
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(x, y, TICKET_WIDTH, TICKET_HEIGHT)
    
    # Position de départ pour le texte
    pdf.set_xy(x + 2, y + 2)
    
    # Titre
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(TICKET_WIDTH - 4, 4, "Mc'INT by Hypnos", align="C")
    
    # Ligne séparatrice
    pdf.line(x + 2, y + 7, x + TICKET_WIDTH - 2, y + 7)
    
    # Nom et horaire (ligne principale)
    pdf.set_xy(x + 2, y + 9)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(TICKET_WIDTH - 4, 5, f"{prenom} {nom} - {horaire}", align="L")
    
    # Téléphone
    pdf.set_xy(x + 2, y + 14)
    pdf.set_font("Helvetica", "", 6)
    pdf.cell(TICKET_WIDTH - 4, 3, f"Tel: {telephone}", align="L")
    
    # Adresse (tronquée si trop longue)
    pdf.set_xy(x + 2, y + 17)
    adresse_short = adresse[:35] + "..." if len(adresse) > 35 else adresse
    pdf.cell(TICKET_WIDTH - 4, 3, adresse_short, align="L")
    
    # Ligne séparatrice
    pdf.line(x + 2, y + 21, x + TICKET_WIDTH - 2, y + 21)
    
    # Produits
    pdf.set_font("Helvetica", "", 7)
    current_y = y + 23
    for p in produits[:3]:  # Max 3 produits affichés
        pdf.set_xy(x + 2, current_y)
        produit_name = p['PRODUIT'][:20] if len(p['PRODUIT']) > 20 else p['PRODUIT']
        pdf.cell(60, 4, f"{p['QTE']}x {produit_name}", align="L")
        pdf.cell(TICKET_WIDTH - 64, 4, f"{p['TOTAL']:.2f}E", align="R")
        current_y += 4
    
    # Total en bas
    pdf.set_xy(x + 2, y + TICKET_HEIGHT - 8)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(TICKET_WIDTH - 4, 5, f"TOTAL: {total:.2f} EUR", align="R")



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
        f"{p['QTE']:<3} {p['PRODUIT']:<14} {p['UNIT']:>4.2f} € {p['TOTAL']:>4.2f} €"
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
    Total: {SUM:.2f} €
    """


if __name__ == "__main__":
    # Test simple
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=12)
    pdf.cell(0, 10, "Test PDF - Mc'INT", ln=True, align="C")
    
    output_path = os.path.join(os.path.dirname(__file__), "output.pdf")
    pdf.output(output_path)
    print(f"PDF généré: {output_path}")