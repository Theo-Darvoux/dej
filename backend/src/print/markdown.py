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


def generate_markdown_for_all_clients(reservations):
    markdown=""
    for reservation in reservations:
        prenom = "Pierre"
        nom = "Caillou"
        telephone = "01 23 45 67 89"
        adresse = "U4 4516"
        
        # Exemple avec plusieurs produits
        produits = [
            {
                "QTE": 1,
                "PRODUIT": "Menu Etudiant",
                "UNIT": 5.50,
                "TOTAL": 5.50
            },
            {
                "QTE": 2,
                "PRODUIT": "Coca-Cola",
                "UNIT": 2.00,
                "TOTAL": 4.00
            },
            {
                "QTE": 1,
                "PRODUIT": "Dessert",
                "UNIT": 3.00,
                "TOTAL": 3.00
            }
        ]
        SUM = 12.50  # Total de tous les produits

        markdown += generate_markdown_for_one_client(
            Prenom=prenom,
            Nom=nom,
            telephone=telephone,
            adresse=adresse,
            produits=produits,
            SUM=SUM
        )
        markdown += "\n\n\n\n\n\n"  # Séparateur entre les clients
    return markdown





#on formate en markdown
def generate_markdown_for_one_client(
    Prenom: str,
    Nom: str,
    telephone: str,
    adresse: str,
    produits: List[Dict[str, Any]],  # Liste de dicts avec clés: QTE, PRODUIT, UNIT, TOTAL
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
    
    A reserver le 12/12/2024 à 14:30
    Pour le client: {Prenom} {Nom}
    email: azerty@telecom-surparis.eu

    ----------------------------------------
    
    Horaire de retrait: 13h/14h
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