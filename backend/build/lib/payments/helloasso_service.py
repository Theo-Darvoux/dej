"""
HelloAsso Service - OAuth2 authentication and Checkout API integration
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.core.config import settings


# Cache for access token
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": None
}


async def get_access_token() -> str:
    """
    Get a valid HelloAsso access token using OAuth2 client credentials.
    Caches the token until it expires.
    """
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            return _token_cache["access_token"]
    
    # Request new token
    token_url = f"{settings.HELLOASSO_URL_TOKEN}/token"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.HELLOASSO_CLIENT_ID,
                "client_secret": settings.HELLOASSO_CLIENT_SECRET,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"HelloAsso auth failed: {response.status_code} - {response.text}")
        
        data = response.json()
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)  # Default 1 hour
        
        # Cache the token (with 5 min buffer)
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 300)
        
        return access_token


async def create_checkout_intent(
    total_amount: int,
    item_name: str,
    payer_email: str,
    payer_first_name: str,
    payer_last_name: str,
    return_url: str,
    error_url: str,
    back_url: str,
    metadata: Optional[Dict] = None,
    contains_donation: bool = False
) -> Dict[str, Any]:
    """
    Create a HelloAsso Checkout Intent.
    
    Args:
        total_amount: Amount in centimes (e.g., 1000 = 10.00€)
        item_name: Description of the purchase
        payer_email: Payer's email
        payer_first_name: Payer's first name
        payer_last_name: Payer's last name
        return_url: URL to redirect after successful payment
        error_url: URL to redirect on error
        back_url: URL to redirect if user wants to go back
        metadata: Optional metadata to attach to the payment
        contains_donation: Whether the payment contains a donation
        
    Returns:
        Dict with 'id' and 'redirectUrl'
    """
    access_token = await get_access_token()
    
    org_slug = settings.HELLOASSO_ORGANIZATION_SLUG
    if not org_slug:
        raise Exception("HELLOASSO_ORGANIZATION_SLUG is not configured")
    
    checkout_url = f"{settings.HELLOASSO_API}/organizations/{org_slug}/checkout-intents"
    
    payload = {
        "totalAmount": total_amount,
        "initialAmount": total_amount,  # Full amount upfront (no installments)
        "itemName": item_name,
        "backUrl": back_url,
        "errorUrl": error_url,
        "returnUrl": return_url,
        "containsDonation": contains_donation,
        "payer": {
            "firstName": payer_first_name,
            "lastName": payer_last_name,
            "email": payer_email
        }
    }
    
    if metadata:
        # HelloAsso requires metadata values to be strings
        payload["metadata"] = {k: str(v) for k, v in metadata.items()}
    
    # Log payload for debugging
    print(f"DEBUG: Create Checkout Payload: {payload}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            checkout_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code not in [200, 201]:
            error_detail = response.text
            try:
                # Try to parse JSON for a cleaner error message if possible
                error_json = response.json()
                if "errors" in error_json:
                    error_detail = f"{response.status_code} - {error_json['errors']}"
            except:
                pass
            print(f"DEBUG: HelloAsso Error Response: {response.status_code} - {error_detail}")
            raise Exception(f"HelloAsso checkout failed: {response.status_code} - {response.text}")
        
        data = response.json()
        return {
            "id": str(data["id"]),
            "redirectUrl": data["redirectUrl"]
        }


async def get_checkout_intent(checkout_intent_id: str) -> Dict[str, Any]:
    """
    Get the status of a checkout intent and associated order/payment info.
    
    Args:
        checkout_intent_id: The ID of the checkout intent
        
    Returns:
        Dict with checkout intent details, order and payment info if completed
    """
    access_token = await get_access_token()
    
    org_slug = settings.HELLOASSO_ORGANIZATION_SLUG
    if not org_slug:
        raise Exception("HELLOASSO_ORGANIZATION_SLUG is not configured")
    
    url = f"{settings.HELLOASSO_API}/organizations/{org_slug}/checkout-intents/{checkout_intent_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"HelloAsso get intent failed: {response.status_code} - {response.text}")
        
        return response.json()
