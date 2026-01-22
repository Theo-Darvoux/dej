"""
Payment Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class CheckoutRequest(BaseModel):
    """Request to create a HelloAsso checkout"""
    amount: int  # Amount in centimes
    item_name: str
    payer_email: EmailStr
    payer_first_name: str
    payer_last_name: str
    reservation_id: Optional[int] = None
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
