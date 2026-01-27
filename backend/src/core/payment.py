from typing import Optional
import httpx
from datetime import datetime, timedelta
from src.core.config import settings


class HelloAssoClient:
    """
    Client pour l'API HelloAsso.
    
    Documentation: https://api.helloasso.com/v5/docs
    - Authentification OAuth2 Client Credentials
    - Création d'un checkout
    - Gestion webhooks pour confirmation paiement
    - Gestion des erreurs
    """
    
    def __init__(self):
        self.client_id = settings.HELLOASSO_CLIENT_ID
        self.client_secret = settings.HELLOASSO_CLIENT_SECRET
        self.token_url = settings.HELLOASSO_URL_TOKEN
        self.api_url = settings.HELLOASSO_API
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """
        Obtient un access token OAuth2 via Client Credentials.
        Cache le token jusqu'à expiration.
        """
        # Réutiliser le token s'il est valide
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Demander un nouveau token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.token_url}/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data["access_token"]
            # Token expire généralement en 1800s (30min), on garde une marge
            expires_in = data.get("expires_in", 1800)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self._access_token
    
    async def create_checkout(
        self,
        amount: int,
        reservation_id: int,
        payer_email: str,
        payer_first_name: str,
        payer_last_name: str,
        item_name: str = "Réservation MC INT"
    ) -> dict:
        """
        Crée un checkout HelloAsso.
        
        Args:
            amount: Montant en centimes (ex: 1000 = 10.00€)
            reservation_id: ID de la réservation
            payer_email: Email du payeur
            payer_first_name: Prénom du payeur
            payer_last_name: Nom du payeur
            item_name: Nom de l'item
        
        Returns:
            dict avec id et redirectUrl
        
        Documentation: https://api.helloasso.com/v5/docs
        """
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/organizations/YOUR_ORG_SLUG/checkout-intents",
                json={
                    "totalAmount": amount,
                    "initialAmount": amount,
                    "itemName": item_name,
                    "backUrl": f"{settings.FRONTEND_URL}/reservations/{reservation_id}",
                    "errorUrl": f"{settings.FRONTEND_URL}/payment/error",
                    "returnUrl": f"{settings.FRONTEND_URL}/payment/success",
                    "containsDonation": False,
                    "payer": {
                        "email": payer_email,
                        "firstName": payer_first_name,
                        "lastName": payer_last_name
                    },
                    "metadata": {
                        "reservation_id": str(reservation_id)
                    }
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def verify_payment(self, payment_id: int) -> dict:
        """
        Vérifie le statut d'un paiement HelloAsso.
        
        Args:
            payment_id: ID du paiement HelloAsso
        
        Returns:
            dict avec state, amount, payer, order, etc.
        
        Documentation: https://api.helloasso.com/v5/docs
        """
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/payments/{payment_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def handle_webhook(self, payload: dict) -> dict:
        """
        Traite un webhook HelloAsso (notification de paiement).
        
        Args:
            payload: Corps du webhook
        
        Returns:
            dict avec les données du paiement traitées
        
        Types de webhooks:
        - Payment: état du paiement (Authorized, Refused, etc.)
        - Order: commande créée
        - Form: formulaire créé/modifié
        
        Documentation: https://api.helloasso.com/v5/docs
        """
        event_type = payload.get("eventType")
        data = payload.get("data", {})
        
        if event_type == "Payment":
            payment_state = data.get("state")
            payment_id = data.get("id")
            amount = data.get("amount")
            order = data.get("order", {})
            payer = data.get("payer", {})
            
            # Extraire les métadonnées personnalisées (ex: reservation_id)
            order_meta = order.get("meta", {})
            
            return {
                "event_type": event_type,
                "payment_id": payment_id,
                "payment_state": payment_state,
                "amount": amount,
                "payer_email": payer.get("email"),
                "payer_name": f"{payer.get('firstName', '')} {payer.get('lastName', '')}",
                "order_id": order.get("id"),
                "order_date": order.get("date"),
                "organization_slug": order.get("organizationSlug"),
            }
        
        return {"event_type": event_type, "data": data}


# Instance globale
helloasso_client = HelloAssoClient()
