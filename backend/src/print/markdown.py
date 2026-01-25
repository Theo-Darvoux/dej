#on appel la base de donnée pour récupérer les infos de la réservation
#on passe pour toutes les réservations
from tokenize import String
from typing import List, Dict, Any
import markdown2
from weasyprint import HTML
from io import BytesIO
import os

def markdown_2_pdf(markdown: str) -> bytes:
    """Convertit du markdown en PDF et retourne les bytes du pdf."""
    # Convertir markdown en HTML
    html_content = markdown2.markdown(markdown)
    
    # Ajouter un style CSS basique pour le formatage
    html_with_style = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Courier New', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                margin: 20px;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Générer le PDF en mémoire
    pdf_buffer = BytesIO()
    HTML(string=html_with_style).write_pdf(pdf_buffer)
    
    # Récupérer les bytes du PDF
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()

    
    return pdf_bytes


def generate_markdown_for_all_clients(reservations: List[Any]):
    markdown = ""
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

        markdown += generate_markdown_for_one_client(
            Prenom=user.prenom or "Inconnu",
            Nom=user.nom or "Inconnu",
            email=user.email,
            telephone=user.phone or "Non renseigné",
            adresse=adresse,
            horaire=user.heure_reservation.strftime("%Hh%M") if user.heure_reservation else "Non renseigné",
            produits=produits,
            SUM=user.total_amount
        )
        markdown += "\n\n\n\n\n\n"  # Séparateur entre les clients
    return markdown


def generate_markdown_for_one_client(
    Prenom: str,
    Nom: str,
    email: str,
    telephone: str,
    adresse: str,
    horaire: str,
    produits: List[Dict[str, Any]],
    SUM: float
):
    # Générer les lignes de produits avec alignement
    produits_lines = "\n    ".join(
        f"{p['QTE']:<3} {p['PRODUIT']:<14} {p['UNIT']:>6.2f} € {p['TOTAL']:>6.2f} €"
        for p in produits
    )

    return f"""
    # CB12
    Restaurant Mc-INT by Hypnos
    Centre commercial Hypnos Industrie
    Tel: 01 23 45 67 89

    ----------------------------------------
    
    A reserver pour le client: {Prenom} {Nom}
    email: {email}

    ----------------------------------------
    
    Horaire de retrait: {horaire}
    Tel: {telephone}
    Adresse: {adresse}

    ----------------------------------------

    QTE PRODUIT          UNIT     TOTAL
    {produits_lines}

    A emporter      Total: {SUM:.2f} €
    """



if __name__ == "__main__":
    # Exemple d'utilisation
    markdown_example = generate_markdown_for_all_clients([0, 1, 2])    
    pdf_bytes = markdown_2_pdf(markdown_example)
    
    # Sauvegarder le PDF avec un chemin absolu
    output_path = os.path.join(os.path.dirname(__file__), "output.pdf")
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)