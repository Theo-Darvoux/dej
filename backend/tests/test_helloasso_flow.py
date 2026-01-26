
import asyncio
import os
import sys

# Ajouter le répertoire parent au path pour importer 'src'
# Ajouter le répertoire parent (backend/) au path pour importer 'src'
current_file_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_file_dir)
sys.path.append(backend_dir)

from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env à la racine (Mc-INT/)
project_root = os.path.dirname(backend_dir)
load_dotenv(os.path.join(project_root, ".env"))

from src.payments import helloasso_service
from src.core.config import settings

async def test_helloasso_flow():
    print("=== Test HelloAsso Flow ===")
    
    # 1. Tester l'obtention du token
    print("\n1. Test get_access_token...")
    try:
        token = await helloasso_service.get_access_token()
        print(f"✅ Token obtenu avec succès ! (Début: {token[:10]}...)")
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du token: {e}")
        return

    # 2. Tester la création d'un Checkout Intent
    print("\n2. Test create_checkout_intent...")
    try:
        # Valeurs de test
        amount = 100  # 1.00€
        item_name = "Menu Antigravity"
        payer_email = "jean.valjean@example.com"
        payer_first_name = "Jean"
        payer_last_name = "Valjean"
        
        # URLs fictives (mais HTTPS comme requis)
        return_url = "https://resa.timothecormier.fr/"
        error_url = "https://resa.timothecormier.fr/"
        back_url = "https://resa.timothecormier.fr/"
        
        metadata = {"id8importante": "12345", "source": "scriptoncheck"}

        result = await helloasso_service.create_checkout_intent(
            total_amount=amount,
            item_name=item_name,
            payer_email=payer_email,
            payer_first_name=payer_first_name,
            payer_last_name=payer_last_name,
            return_url=return_url,
            error_url=error_url,
            back_url=back_url,
            metadata=metadata
        )
        
        print(f"✅ Checkout Intent créé avec succès !")
        print(f"   ID: {result['id']}")
        print(f"   Type ID: {type(result['id'])}")
        print(f"   URL de redirection: {result['redirectUrl']}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du checkout: {e}")

if __name__ == "__main__":
    asyncio.run(test_helloasso_flow())
