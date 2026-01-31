"""
Payment Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class CheckoutRequest(BaseModel):
    """Request to create a HelloAsso checkout"""
    payer_email: EmailStr
    payer_first_name: str
    payer_last_name: str
    reservation_id: int  # Required - no fallback to email lookup
    metadata: Optional[Dict[str, Any]] = None


class CheckoutResponse(BaseModel):
    """Response from checkout creation"""
    redirect_url: str
    checkout_intent_id: str


class PaymentVerifyRequest(BaseModel):
    """Request to verify a payment"""
    checkout_intent_id: str


class PaymentVerifyResponse(BaseModel):
    """Response from payment verification"""
    success: bool
    order_id: Optional[int] = None
    payment_id: Optional[int] = None
    amount: Optional[int] = None
    payer_email: Optional[str] = None
    message: Optional[str] = None
    status_token: Optional[str] = None  # Token pour accéder à la page de statut


class PaymentStatusResponse(BaseModel):
    """Response from status check endpoint"""
    payment_status: str  # "pending", "completed", "failed"
    status_token: Optional[str] = None
    checkout_intent_id: str

