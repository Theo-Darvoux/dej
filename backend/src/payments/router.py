"""
Payment Router - HelloAsso Checkout endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from src.payments.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentStatusResponse
)
from src.payments import helloasso_service
from src.core.config import settings
from src.auth.service import normalize_email
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import secrets

router = APIRouter(prefix="/payments", tags=["Payments"])


async def complete_payment(user, checkout_intent_id: str, db: Session) -> bool:
    """
    Mark a payment as completed and send confirmation email.
    Returns True if this was a new completion, False if already completed.

    This function is used by:
    - /status/{checkout_intent_id} endpoint (frontend polling)
    - /verify/{checkout_intent_id} endpoint (legacy)
    - /webhook endpoint (HelloAsso callback)
    - Background task (periodic checking)
    """
    from src.mail import send_order_confirmation

    if user.payment_status == "completed":
        print(f"[DEBUG] complete_payment: user {user.id} already completed, skipping")
        return False  # Already done

    print(f"[DEBUG] complete_payment: completing payment for user {user.id}")

    user.payment_status = "completed"
    user.payment_intent_id = checkout_intent_id
    user.payment_date = datetime.now(timezone.utc)

    if not user.status_token:
        user.status_token = secrets.token_urlsafe(32)

    db.commit()
    db.refresh(user)

    # Send confirmation email
    try:
        print(f"[DEBUG] complete_payment: sending confirmation email to {user.email}")
        email_sent = await send_order_confirmation(user)
        if email_sent:
            print(f"[DEBUG] complete_payment: email sent successfully to {user.email}")
        else:
            print(f"[WARNING] complete_payment: email failed for {user.email}")
        # Save any changes from email (status_token if modified)
        db.commit()
    except Exception as e:
        print(f"[ERROR] complete_payment: exception during email send: {e}")

    return True


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
        db = SessionLocal()
        try:
            user = None

            # Strategy 1: Find by reservation_id if provided
            if checkout_request.reservation_id:
                user = db.query(User).filter(User.id == checkout_request.reservation_id).first()
                if user:
                    print(f"[DEBUG] Found user by reservation_id: {user.id}")

            # Strategy 2: Fallback to finding by email with pending payment
            if not user and checkout_request.payer_email:
                from src.auth.service import normalize_email
                try:
                    _, identity = normalize_email(checkout_request.payer_email)
                except Exception:
                    identity = None

                query = db.query(User).filter(
                    User.menu_id.isnot(None),  # Has an order
                    User.payment_status.in_([None, "pending"]),  # Not yet paid
                )
                if identity:
                    query = query.filter(
                        or_(
                            User.normalized_email == identity,
                            User.email == checkout_request.payer_email
                        )
                    )
                else:
                    query = query.filter(User.email == checkout_request.payer_email)

                user = query.order_by(User.created_at.desc()).first()
                if user:
                    print(f"[DEBUG] Found user by email fallback: {user.id} ({user.email})")

            if user:
                user.payment_intent_id = checkout_intent_id
                # Generate status_token if missing
                if not user.status_token:
                    user.status_token = secrets.token_urlsafe(32)
                db.commit()
                print(f"[DEBUG] Stored checkout_intent_id {checkout_intent_id} for user {user.id}")
            else:
                print(f"[WARNING] No user found for checkout (reservation_id: {checkout_request.reservation_id}, email: {checkout_request.payer_email})")
        finally:
            db.close()

        return CheckoutResponse(
            redirect_url=result["redirectUrl"],
            checkout_intent_id=checkout_intent_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{checkout_intent_id}", response_model=PaymentStatusResponse)
async def get_payment_status(checkout_intent_id: str):
    """
    Get payment status by polling HelloAsso API.
    Updates database if payment is newly completed.

    This is the primary endpoint for frontend polling after payment return.
    """
    from src.db.session import SessionLocal
    from src.users.models import User

    db = SessionLocal()
    try:
        # Find user by payment_intent_id (stored during checkout creation)
        user = db.query(User).filter(User.payment_intent_id == checkout_intent_id).first()

        if not user:
            print(f"[DEBUG] get_payment_status: no user found for intent {checkout_intent_id}")
            raise HTTPException(status_code=404, detail="Commande introuvable")

        print(f"[DEBUG] get_payment_status: found user {user.id}, current status: {user.payment_status}")

        # If already completed, return immediately without calling HelloAsso
        if user.payment_status == "completed":
            return PaymentStatusResponse(
                payment_status="completed",
                status_token=user.status_token,
                checkout_intent_id=checkout_intent_id
            )

        # Query HelloAsso API for current status
        try:
            result = await helloasso_service.get_checkout_intent(checkout_intent_id)
            print(f"[DEBUG] get_payment_status: HelloAsso result keys: {list(result.keys())}")

            order = result.get("order")

            if order:
                # Payment completed - update user
                await complete_payment(user, checkout_intent_id, db)

                return PaymentStatusResponse(
                    payment_status="completed",
                    status_token=user.status_token,
                    checkout_intent_id=checkout_intent_id
                )
            else:
                # Still pending
                return PaymentStatusResponse(
                    payment_status="pending",
                    status_token=None,
                    checkout_intent_id=checkout_intent_id
                )

        except Exception as e:
            print(f"[ERROR] get_payment_status: HelloAsso API error: {e}")
            # Return current DB status on API error
            return PaymentStatusResponse(
                payment_status=user.payment_status or "pending",
                status_token=user.status_token,
                checkout_intent_id=checkout_intent_id
            )

    finally:
        db.close()


@router.get("/verify/{checkout_intent_id}", response_model=PaymentVerifyResponse)
async def verify_payment(checkout_intent_id: str):
    """
    Verify a payment after user returns from HelloAsso.
    Checks the checkout intent status and returns order/payment info.
    """
    from src.db.session import SessionLocal
    from src.users.models import User
    from src.mail import send_order_confirmation

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
                    user = db.query(User).filter(User.id == int(res_id)).first()
                    if user:
                        print(f"[DEBUG] User found by reservation_id: {user.id} ({user.email})")

                # Strategy 2: Find by checkout_intent_id stored in payment_intent_id
                if not user:
                    print(f"[DEBUG] Attempting to find user by checkout_intent_id: {checkout_intent_id}")
                    user = db.query(User).filter(User.payment_intent_id == checkout_intent_id).first()
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
                    query = db.query(User).filter(
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
                    print(f"[DEBUG] User {user.id} data: total={user.total_amount}, menu={user.menu_id}, drink={user.boisson_id}, extras={user.bonus_ids}, payment_status={user.payment_status}")

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


@router.get("/webhook")
async def webhook_test():
    """Test endpoint to verify webhook URL is accessible."""
    print("[WEBHOOK] GET request received - webhook URL is accessible")
    return {"status": "ok", "message": "Webhook endpoint is accessible. Use POST for actual webhooks."}


@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Webhook endpoint for HelloAsso notifications.
    HelloAsso will POST here when a payment is completed.

    This is a backup confirmation method - the primary method is frontend
    polling via /status/{checkout_intent_id} and the background task.
    """
    from src.db.session import SessionLocal
    from src.users.models import User

    # Log immédiatement que la requête est arrivée
    print(f"[WEBHOOK] ========== INCOMING REQUEST ==========")
    print(f"[WEBHOOK] Method: {request.method}")
    print(f"[WEBHOOK] URL: {request.url}")
    print(f"[WEBHOOK] Client: {request.client}")
    print(f"[WEBHOOK] Headers: {dict(request.headers)}")

    try:
        raw_body = await request.body()
        print(f"[WEBHOOK] Raw body length: {len(raw_body)} bytes")
        print(f"[WEBHOOK] Raw body preview: {raw_body[:500] if raw_body else 'EMPTY'}")

        import json
        body = json.loads(raw_body) if raw_body else {}

        event_type = body.get("eventType")
        data = body.get("data", {})

        # Log the webhook for debugging
        print(f"[WEBHOOK] HelloAsso event: {event_type}")

        # Handle different event types
        if event_type == "Payment":
            # A payment was made
            order_id = data.get("order", {}).get("id")
            checkout_intent_id = data.get("checkoutIntentId")
            metadata = data.get("metadata", {})
            res_id = metadata.get("reservation_id")

            print(f"[WEBHOOK] Payment event - order_id: {order_id}, checkout_intent_id: {checkout_intent_id}, res_id: {res_id}")

            db = SessionLocal()
            try:
                user = None

                # Strategy 1: Find by reservation_id from metadata
                if res_id:
                    user = db.query(User).filter(User.id == int(res_id)).first()
                    if user:
                        print(f"[WEBHOOK] Found user by reservation_id: {user.id}")

                # Strategy 2: Find by checkout_intent_id
                if not user and checkout_intent_id:
                    user = db.query(User).filter(User.payment_intent_id == checkout_intent_id).first()
                    if user:
                        print(f"[WEBHOOK] Found user by checkout_intent_id: {user.id}")

                if user:
                    intent_id = checkout_intent_id or user.payment_intent_id or f"ORDER_{order_id}"
                    was_new = await complete_payment(user, intent_id, db)
                    if was_new:
                        print(f"[WEBHOOK] Payment completed for user {user.id} ({user.email})")
                    else:
                        print(f"[WEBHOOK] User {user.id} was already completed")
                else:
                    print(f"[WEBHOOK] No user found for this payment (res_id: {res_id}, intent: {checkout_intent_id})")

            finally:
                db.close()

        return {"status": "ok"}

    except Exception as e:
        print(f"[WEBHOOK] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
