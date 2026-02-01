"""
Payment Router - HelloAsso Checkout endpoints

Features:
- Race condition protection for payment completion
- Background email sending to avoid blocking responses
- Idempotent payment completion
"""
import asyncio
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
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
import secrets
import traceback

router = APIRouter(prefix="/payments", tags=["Payments"])

# Lock for payment completion to prevent race conditions
# Each entry stores (lock, last_used_timestamp)
_payment_locks: dict[int, tuple[asyncio.Lock, float]] = {}
_locks_lock = asyncio.Lock()
_LOCK_TTL_SECONDS = 3600  # 1 hour


async def _cleanup_old_locks():
    """Remove locks older than TTL to prevent memory leaks."""
    import time
    current_time = time.time()
    to_remove = []

    for user_id, (lock, last_used) in _payment_locks.items():
        if current_time - last_used > _LOCK_TTL_SECONDS and not lock.locked():
            to_remove.append(user_id)

    for user_id in to_remove:
        del _payment_locks[user_id]

    if to_remove:
        print(f"[DEBUG] Cleaned up {len(to_remove)} expired payment locks")


async def _get_user_lock(user_id: int) -> asyncio.Lock:
    """Get or create a lock for a specific user."""
    import time
    async with _locks_lock:
        # Cleanup old locks periodically (every time we access locks)
        if len(_payment_locks) > 100:  # Only cleanup if we have many locks
            await _cleanup_old_locks()

        current_time = time.time()
        if user_id not in _payment_locks:
            _payment_locks[user_id] = (asyncio.Lock(), current_time)
        else:
            # Update last used time
            lock, _ = _payment_locks[user_id]
            _payment_locks[user_id] = (lock, current_time)
        return _payment_locks[user_id][0]


async def _send_confirmation_email_background(user_id: int, user_email: str):
    """
    Send confirmation email in background without blocking the response.

    Args:
        user_id: User ID to look up fresh data
        user_email: Email for logging purposes
    """
    from src.db.session import SessionLocal
    from src.users.models import User
    from src.mail import send_order_confirmation

    try:
        print(f"[BACKGROUND_EMAIL] Sending confirmation to {user_email}")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.payment_status == "completed":
                email_sent = await send_order_confirmation(user)
                if email_sent:
                    user.email_delivery_status = "sent"
                    print(f"[BACKGROUND_EMAIL] Email sent successfully to {user_email}")
                else:
                    user.email_delivery_status = "failed"
                    print(f"[BACKGROUND_EMAIL] Email failed for {user_email}")
                db.commit()  # Save email delivery status
        finally:
            db.close()

    except Exception as e:
        # Try to update delivery status even on exception
        try:
            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.email_delivery_status = "failed"
                db.commit()
            db.close()
        except Exception:
            pass
        print(f"[BACKGROUND_EMAIL] Exception sending email to {user_email}: {e}")
        traceback.print_exc()


async def complete_payment(user, checkout_intent_id: str, db: Session) -> bool:
    """
    Mark a payment as completed and send confirmation email in background.
    Returns True if this was a new completion, False if already completed.

    This function is used by:
    - /status/{checkout_intent_id} endpoint (frontend polling)
    - /verify/{checkout_intent_id} endpoint (legacy)
    - Background task (periodic checking)

    Uses per-user locking to prevent race conditions.
    """
    # Get user-specific lock to prevent concurrent updates
    user_lock = await _get_user_lock(user.id)

    async with user_lock:
        # Re-check status inside the lock (double-checked locking pattern)
        db.refresh(user)

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

    # Send confirmation email in background (outside the lock)
    asyncio.create_task(
        _send_confirmation_email_background(user.id, user.email)
    )

    return True


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, checkout_request: CheckoutRequest):
    """
    Create a HelloAsso Checkout Intent.
    Returns a redirect URL to send the user to HelloAsso payment page.
    """
    from src.db.session import SessionLocal
    from src.users.models import User

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
            # Find user by reservation_id (required, no email fallback for security)
            user = db.query(User).filter(User.id == checkout_request.reservation_id).first()

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="Réservation introuvable"
                )

            print(f"[DEBUG] Found user by reservation_id: {user.id}")

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

                # No email fallback for security - user must be found by reservation_id or checkout_intent_id
                if not user:
                    print(f"[ERROR] No user found for payment (intent: {checkout_intent_id}, res_id: {res_id})")

                if user:
                    # Log what we found to debug empty emails
                    print(f"[DEBUG] User {user.id} data: total={user.total_amount}, menu={user.menu_id}, drink={user.boisson_id}, extras={user.bonus_ids}, payment_status={user.payment_status}")

                    # Complete payment with race condition protection
                    was_new = await complete_payment(user, checkout_intent_id, db)
                    if was_new:
                        print(f"[DEBUG] Payment completed for user {user.id}")
                    else:
                        print(f"[DEBUG] Payment already completed for user {user.id}")

                    # Refresh to get latest data including status_token
                    db.refresh(user)
                    status_token = user.status_token
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
        traceback.print_exc()
        return PaymentVerifyResponse(
            success=False,
            message=str(e)
        )
