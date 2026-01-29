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
from src.auth.service import normalize_email
from sqlalchemy import or_

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, checkout_request: CheckoutRequest):
    """
    Create a HelloAsso Checkout Intent.
    Returns a redirect URL to send the user to HelloAsso payment page.
    """
    from src.db.session import SessionLocal
    from src.users.models import User
    import secrets

    try:
        # Build URLs for HelloAsso redirects (must be HTTPS!)
        # Use HELLOASSO_REDIRECT_BASE_URL if set, otherwise fall back to FRONTEND_URL
        redirect_base = settings.HELLOASSO_REDIRECT_BASE_URL
        if not redirect_base:
            redirect_base = settings.FRONTEND_URL or "http://localhost:5173"

        # Remove trailing slash to avoid double slashes
        redirect_base = redirect_base.rstrip('/')

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

        checkout_intent_id = result["id"]

        # Store checkout_intent_id on user for later retrieval
        # This is crucial since HelloAsso may not return metadata in GET requests
        if checkout_request.reservation_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == checkout_request.reservation_id).first()
                if user:
                    user.payment_intent_id = checkout_intent_id
                    # Generate status_token if missing
                    if not user.status_token:
                        user.status_token = secrets.token_urlsafe(32)
                    db.commit()
                    print(f"[DEBUG] Stored checkout_intent_id {checkout_intent_id} for user {user.id}")
            finally:
                db.close()

        return CheckoutResponse(
            redirect_url=result["redirectUrl"],
            checkout_intent_id=checkout_intent_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{checkout_intent_id}", response_model=PaymentVerifyResponse)
async def verify_payment(checkout_intent_id: str):
    """
    Verify a payment after user returns from HelloAsso.
    Checks the checkout intent status and returns order/payment info.
    """
    from src.db.session import SessionLocal
    from src.users.models import User
    from src.mail import send_order_confirmation
    from sqlalchemy.orm import joinedload
    from datetime import datetime, timezone
    import secrets

    try:
        print(f"[DEBUG] Verifying payment for intent: {checkout_intent_id}")
        result = await helloasso_service.get_checkout_intent(checkout_intent_id)
        
        print(f"[DEBUG] HelloAsso result keys: {list(result.keys())}")
        metadata = result.get('metadata', {})
        print(f"[DEBUG] Metadata: {metadata}")
        
        # Check if we have an order (payment was successful)
        order = result.get("order")
        status_token = None
        
        if order:
            order_id = order.get('id')
            payer_email = order.get("payer", {}).get("email")
            print(f"[DEBUG] Order found, ID: {order_id}, Payer: {payer_email}")
            
            # Update database if not already done by webhook
            res_id = metadata.get("reservation_id")
            
            print(f"[DEBUG] reservation_id from metadata: {res_id} (type: {type(res_id)})")
            
            db = SessionLocal()
            try:
                user = None

                # Strategy 1: Find by reservation_id from metadata
                if res_id:
                    user = db.query(User).options(
                        joinedload(User.menu_item),
                        joinedload(User.boisson_item),
                        joinedload(User.bonus_item)
                    ).filter(User.id == int(res_id)).first()
                    if user:
                        print(f"[DEBUG] User found by reservation_id: {user.id} ({user.email})")

                # Strategy 2: Find by checkout_intent_id stored in payment_intent_id
                if not user:
                    print(f"[DEBUG] Attempting to find user by checkout_intent_id: {checkout_intent_id}")
                    user = db.query(User).options(
                        joinedload(User.menu_item),
                        joinedload(User.boisson_item),
                        joinedload(User.bonus_item)
                    ).filter(User.payment_intent_id == checkout_intent_id).first()
                    if user:
                        print(f"[DEBUG] User found by checkout_intent_id: {user.id} ({user.email})")

                # Strategy 3: Find by payer email (more lenient than before)
                if not user and payer_email:
                    print(f"[DEBUG] Attempting fallback: finding user by payer email {payer_email}")

                    # Normaliser l'email pour la recherche par identité
                    identity = None
                    try:
                        _, identity = normalize_email(payer_email)
                    except Exception as e:
                        print(f"[DEBUG] Could not normalize email: {e}")

                    # Recherche robuste : user avec commande valide
                    # Don't require payment_status == "pending" anymore (webhook may have changed it)
                    query = db.query(User).options(
                        joinedload(User.menu_item),
                        joinedload(User.boisson_item),
                        joinedload(User.bonus_item)
                    ).filter(
                        User.menu_id.isnot(None),          # A une commande
                        User.total_amount > 0,             # Montant valide
                    )

                    # Chercher par identité normalisée OU email exact
                    if identity:
                        query = query.filter(
                            or_(
                                User.normalized_email == identity,
                                User.email == payer_email
                            )
                        )
                    else:
                        query = query.filter(User.email == payer_email)

                    # Vérifier que la réservation n'est pas expirée
                    query = query.filter(
                        or_(
                            User.reservation_expires_at.is_(None),
                            User.reservation_expires_at > datetime.now(timezone.utc)
                        )
                    )

                    # Prioritize users without completed payment, then by creation date
                    user = query.order_by(
                        (User.payment_status != "completed").desc(),
                        User.created_at.desc()
                    ).first()

                    if user:
                        print(f"[DEBUG] User found by email fallback: {user.id} (identity: {identity}, status: {user.payment_status})")
                    else:
                        print(f"[WARNING] No valid user found for email {payer_email} (identity: {identity})")

                if user:
                    # Refresh to ensure we have the latest data from DB (in case of concurrent updates)
                    db.refresh(user)

                    # Log what we found to debug empty emails
                    print(f"[DEBUG] User {user.id} data: total={user.total_amount}, menu={user.menu_id}, drink={user.boisson_id}, bonus={user.bonus_id}, payment_status={user.payment_status}")

                    # Générer status_token si absent (CRITICAL for order tracking)
                    if not user.status_token:
                        print(f"[DEBUG] Generating new status_token for user {user.id}")
                        user.status_token = secrets.token_urlsafe(32)
                        db.commit()
                    status_token = user.status_token

                    if user.payment_status != "completed":
                        print(f"[DEBUG] Updating payment status to completed for user {user.id}")
                        user.payment_status = "completed"
                        user.payment_intent_id = checkout_intent_id
                        user.payment_date = datetime.now(timezone.utc)
                        db.commit()
                        db.refresh(user)

                        # Envoyer l'email de confirmation
                        try:
                            print(f"[DEBUG] Sending order confirmation email to {user.email}")
                            email_sent = await send_order_confirmation(user)
                            if email_sent:
                                print(f"[DEBUG] Confirmation email sent successfully to {user.email}")
                            else:
                                print(f"[WARNING] Confirmation email failed for {user.email}")
                            # Sauvegarder le status_token si modifié par l'email
                            db.commit()
                        except Exception as e:
                            print(f"[ERROR] Exception during envoi email: {e}")
                    else:
                        print(f"[DEBUG] Payment already completed for user {user.id}, skipping email")
                else:
                    print(f"[ERROR] No user found for this payment (intent: {checkout_intent_id})")

            finally:
                db.close()

            # Payment successful
            return PaymentVerifyResponse(
                success=True,
                order_id=order_id,
                amount=order.get("amount", {}).get("total"),
                payer_email=payer_email,
                message="Paiement réussi",
                status_token=status_token
            )
        else:
            # No order yet - payment pending or failed
            print(f"[DEBUG] No order found for intent {checkout_intent_id}. result: {result.get('status')}")
            return PaymentVerifyResponse(
                success=False,
                message="Paiement en attente ou non complété"
            )
            
    except Exception as e:
        print(f"[ERROR] Exception in verify_payment: {e}")
        import traceback
        traceback.print_exc()
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
    from src.db.session import SessionLocal
    from src.users.models import User
    from src.mail import send_order_confirmation
    from datetime import datetime, timezone

    try:
        body = await request.json()
        
        event_type = body.get("eventType")
        data = body.get("data", {})
        
        # Log the webhook for debugging
        print(f"HelloAsso Webhook: {event_type}")
        
        # Handle different event types
        if event_type == "Payment":
            # A payment was made
            order_id = data.get("order", {}).get("id")
            
            # Fetch the checkout intent to get metadata
            # Note: The webhook data might not contain metadata directly depending on HelloAsso version
            # It's safer to fetch the intent if it's not in the 'data'
            checkout_intent_id = data.get("checkoutIntentId") # Verify if this is in the webhook payload
            
            # Fallback/Alternative: use order metadata if available
            metadata = data.get("metadata", {})
            res_id = metadata.get("reservation_id")
            
            if res_id:
                db = SessionLocal()
                try:
                    from sqlalchemy.orm import joinedload
                    user = db.query(User).options(
                        joinedload(User.menu_item),
                        joinedload(User.boisson_item),
                        joinedload(User.bonus_item)
                    ).filter(User.id == int(res_id)).first()
                    
                    if user and user.payment_status != "completed":
                        user.payment_status = "completed"
                        user.payment_intent_id = checkout_intent_id or f"ORDER_{order_id}"
                        user.payment_date = datetime.now(timezone.utc)
                        db.commit()
                        db.refresh(user)
                        
                        print(f"[DEBUG] Webhook: Sending order confirmation email to {user.email}")
                        # Envoyer l'email de confirmation
                        await send_order_confirmation(user)
                        print(f"DEBUG: Reservation {res_id} updated via Webhook")
                finally:
                    db.close()
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
