"""
HelloAsso Service - OAuth2 authentication and Checkout API integration

Features:
- Thread-safe token caching with asyncio.Lock
- Persistent HTTP client with connection pooling
- Retry logic with exponential backoff for transient failures
- Configurable timeouts on all API calls
"""
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.core.config import settings


# Configuration
API_TIMEOUT = 30.0  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds

# Persistent HTTP client with connection pooling
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()

# Cache for OAuth tokens with thread-safe access
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": None
}
_token_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the persistent HTTP client."""
    global _http_client

    async with _client_lock:
        if _http_client is None or _http_client.is_closed:
            _http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(API_TIMEOUT),
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                ),
            )
        return _http_client


async def close_http_client():
    """Close the HTTP client. Call on application shutdown."""
    global _http_client
    async with _client_lock:
        if _http_client is not None and not _http_client.is_closed:
            await _http_client.aclose()
            _http_client = None


def _update_token_cache(data: dict) -> str:
    """Update the token cache with new token data."""
    global _token_cache
    _token_cache["access_token"] = data["access_token"]
    _token_cache["refresh_token"] = data.get("refresh_token")
    expires_in = data.get("expires_in", 3600)
    # Cache with 5 min buffer before expiration
    _token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 300)
    return _token_cache["access_token"]


async def _request_token_with_credentials() -> str:
    """Request a new token using client credentials grant."""
    token_url = f"{settings.HELLOASSO_URL_TOKEN}/token"
    client = await get_http_client()

    response = await client.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.HELLOASSO_CLIENT_ID,
            "client_secret": settings.HELLOASSO_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        raise Exception(f"HelloAsso auth failed: {response.status_code} - {response.text}")

    return _update_token_cache(response.json())


async def _refresh_access_token() -> str:
    """Refresh the access token using the refresh token."""
    global _token_cache
    token_url = f"{settings.HELLOASSO_URL_TOKEN}/token"
    client = await get_http_client()

    response = await client.post(
        token_url,
        data={
            "grant_type": "refresh_token",
            "client_id": settings.HELLOASSO_CLIENT_ID,
            "refresh_token": _token_cache["refresh_token"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        # Clear invalid refresh token
        _token_cache["refresh_token"] = None
        raise Exception(f"HelloAsso refresh failed: {response.status_code}")

    return _update_token_cache(response.json())


async def get_access_token() -> str:
    """
    Get a valid HelloAsso access token.

    Uses cached token if valid, otherwise:
    1. Tries to refresh using refresh_token
    2. Falls back to client_credentials if refresh fails

    Thread-safe with asyncio.Lock to prevent race conditions.
    """
    global _token_cache

    async with _token_lock:
        # Check if we have a valid cached token
        if _token_cache["access_token"] and _token_cache["expires_at"]:
            if datetime.now() < _token_cache["expires_at"]:
                return _token_cache["access_token"]

        # Try refresh token first if available
        if _token_cache["refresh_token"]:
            try:
                return await _refresh_access_token()
            except Exception:
                pass  # Fall back to client_credentials

        # Request new token with client credentials
        return await _request_token_with_credentials()


async def _request_with_retry(
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """
    Make an HTTP request with retry logic and exponential backoff.

    Retries on:
    - Network errors (connection timeouts, etc.)
    - 5xx server errors
    - 429 rate limit errors
    """
    client = await get_http_client()
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Retry on server errors or rate limiting
            if response.status_code >= 500 or response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                    print(f"[HELLOASSO] Retry {attempt + 1}/{MAX_RETRIES} after {response.status_code}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

            return response

        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                print(f"[HELLOASSO] Retry {attempt + 1}/{MAX_RETRIES} after {type(e).__name__}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                raise

    if last_exception:
        raise last_exception
    raise Exception("Request failed after all retries")


async def create_checkout_intent(
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
    Create a HelloAsso Checkout Intent for breakfast order.

    Note: All breakfast menus cost 1€, supplements are free.

    Args:
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

    # Prix fixe: tous les menus petit-déjeuner coûtent 1€, suppléments gratuits
    payload = {
        "totalAmount": 100,  # 100 centimes = 1€
        "initialAmount": 100,
        "itemName": settings.HELLOASSO_ITEM_NAME,
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

    response = await _request_with_retry(
        "POST",
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
            error_json = response.json()
            if "errors" in error_json:
                error_detail = f"{response.status_code} - {error_json['errors']}"
        except (ValueError, KeyError):
            pass  # Response is not valid JSON, use raw text
        print(f"DEBUG: HelloAsso Error Response: {response.status_code} - {error_detail}")
        raise Exception(f"Il y a un problème avec HelloAsso. Veuillez réessayer plus tard.")

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

    response = await _request_with_retry(
        "GET",
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if response.status_code != 200:
        raise Exception(f"HelloAsso get intent failed: {response.status_code} - {response.text}")

    return response.json()
