"""
Service de paiement HelloAsso

TODO: À implémenter avec la documentation HelloAsso
"""

from typing import Optional
from src.core.config import settings


class HelloAssoClient:
    """
    Client pour l'API HelloAsso.
    
    Documentation à recevoir pour implémenter:
    - Authentification (OAuth2 ?)
    - Création d'un intent/checkout
    - Gestion webhooks pour confirmation paiement
    - Gestion des erreurs
    """
    
    def __init__(self):
        self.api_url = settings.HELLOASSO_API_URL
        self.api_key = settings.HELLOASSO_API_KEY
    
    async def create_payment_intent(
        self,
        amount: float,
        reservation_id: int,
        user_email: str
    ) -> dict:
        """
        Crée un intent de paiement HelloAsso.
        
        Args:
            amount: Montant en euros
            reservation_id: ID de la réservation
            user_email: Email de l'utilisateur
        
        Returns:
            dict avec intent_id et redirect_url
        
        TODO: Implémenter avec doc HelloAsso
        """
        raise NotImplementedError("HelloAsso payment à implémenter avec la doc")
    
    async def verify_payment(self, intent_id: str) -> dict:
        """
        Vérifie le statut d'un paiement.
        
        Args:
            intent_id: ID de l'intent HelloAsso
        
        Returns:
            dict avec status, amount, etc.
        
        TODO: Implémenter avec doc HelloAsso
        """
        raise NotImplementedError("HelloAsso verification à implémenter avec la doc")
    
    async def handle_webhook(self, payload: dict) -> dict:
        """
        Traite un webhook HelloAsso (confirmation paiement).
        
        Args:
            payload: Corps du webhook
        
        Returns:
            dict avec les données du paiement
        
        TODO: Implémenter avec doc HelloAsso
        """
        raise NotImplementedError("HelloAsso webhook à implémenter avec la doc")


# Instance globale
helloasso_client = HelloAssoClient()
