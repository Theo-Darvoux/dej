"""
Payment Router - HelloAsso Checkout endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from src.payments.schemas import (
    CheckoutRequest, 
    CheckoutResponse, 
    PaymentVerifyRequest,
    PaymentVerifyResponse
)
from src.payments import helloasso_service
from src.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, checkout_request: CheckoutRequest):
    """
    Create a HelloAsso Checkout Intent.
    Returns a redirect URL to send the user to HelloAsso payment page.
    """
    try:
        # Build URLs for HelloAsso redirects (must be HTTPS!)
        # Use HELLOASSO_REDIRECT_BASE_URL if set, otherwise fall back to FRONTEND_URL
        redirect_base = settings.HELLOASSO_REDIRECT_BASE_URL
        if not redirect_base:
            redirect_base = settings.FRONTEND_URL or "http://localhost:5173"
        
        # Ensure HTTPS for HelloAsso (required by their API)
        if not redirect_base.startswith("https://"):
            raise HTTPException(
                status_code=400, 
                detail="HelloAsso requiert une URL HTTPS. Configure HELLOASSO_REDIRECT_BASE_URL dans .env"
            )
        
        return_url = f"{redirect_base}/payment/success"
        error_url = f"{redirect_base}/payment/error"
        back_url = f"{redirect_base}/order"
        
        # Build metadata
        metadata = checkout_request.metadata or {}
        if checkout_request.reservation_id:
            metadata["reservation_id"] = checkout_request.reservation_id
        
        # Create checkout intent
        result = await helloasso_service.create_checkout_intent(
            total_amount=checkout_request.amount,
            item_name=checkout_request.item_name,
            payer_email=checkout_request.payer_email,
            payer_first_name=checkout_request.payer_first_name,
            payer_last_name=checkout_request.payer_last_name,
            return_url=return_url,
            error_url=error_url,
            back_url=back_url,
            metadata=metadata,
            contains_donation=False
        )
        
        return CheckoutResponse(
            redirect_url=result["redirectUrl"],
            checkout_intent_id=result["id"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{checkout_intent_id}", response_model=PaymentVerifyResponse)
async def verify_payment(checkout_intent_id: str):
    """
    Verify a payment after user returns from HelloAsso.
    Checks the checkout intent status and returns order/payment info.
    """
    try:
        result = await helloasso_service.get_checkout_intent(checkout_intent_id)
        
        # Check if we have an order (payment was successful)
        order = result.get("order")
        
        if order:
            # Payment successful
            return PaymentVerifyResponse(
                success=True,
                order_id=order.get("id"),
                amount=order.get("amount", {}).get("total"),
                payer_email=order.get("payer", {}).get("email"),
                message="Paiement réussi"
            )
        else:
            # No order yet - payment pending or failed
            return PaymentVerifyResponse(
                success=False,
                message="Paiement en attente ou non complété"
            )
            
    except Exception as e:
        return PaymentVerifyResponse(
            success=False,
            message=str(e)
        )


@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Webhook endpoint for HelloAsso notifications.
    HelloAsso will POST here when a payment is completed.
    """
    try:
        body = await request.json()
        
        event_type = body.get("eventType")
        data = body.get("data", {})
        
        # Log the webhook for debugging
        print(f"HelloAsso Webhook: {event_type}")
        print(f"Data: {data}")
        
        # Handle different event types
        if event_type == "Payment":
            # A payment was made
            payment_id = data.get("id")
            order_id = data.get("order", {}).get("id")
            amount = data.get("amount")
            payer = data.get("payer", {})
            
            print(f"Payment received: {payment_id}, Order: {order_id}, Amount: {amount}")
            
            # TODO: Update your reservation/order status in the database
            # You can use metadata to link back to your reservation_id
            
        elif event_type == "Order":
            # An order was created
            order_id = data.get("id")
            print(f"Order created: {order_id}")
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
