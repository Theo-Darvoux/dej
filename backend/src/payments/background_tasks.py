"""
Background Tasks for Payment Processing

This module contains async background tasks that run periodically to check
pending payments against the HelloAsso API.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload

# Interval between payment checks (in seconds)
PAYMENT_CHECK_INTERVAL = 300


async def check_pending_payments():
    """
    Background task that checks HelloAsso API for all pending payments.
    Runs every 60 seconds.

    This provides a safety net for payments that:
    - User closed browser before returning from payment
    - Webhook failed to fire or was delayed
    - Network issues prevented frontend polling from completing
    """
    from src.db.session import SessionLocal
    from src.users.models import User
    from src.payments import helloasso_service
    from src.payments.router import complete_payment

    print(f"[BACKGROUND] Payment check task started (interval: {PAYMENT_CHECK_INTERVAL}s)")

    while True:
        try:
            db = SessionLocal()
            try:
                # Find all users with pending payments
                # Only check payments that have a checkout_intent_id
                # Find all users with pending payments
                # Only check payments that have a checkout_intent_id
                pending_users = db.query(User).filter(
                    User.payment_status == "pending",
                    User.payment_intent_id.isnot(None)
                ).all()

                if pending_users:
                    print(f"[BACKGROUND] Checking {len(pending_users)} pending payments")

                for user in pending_users:
                    try:
                        # Query HelloAsso for this checkout intent
                        result = await helloasso_service.get_checkout_intent(user.payment_intent_id)
                        order = result.get("order")

                        if order:
                            # Payment completed - update user
                            was_new = await complete_payment(user, user.payment_intent_id, db)
                            if was_new:
                                print(f"[BACKGROUND] Payment completed for user {user.id} ({user.email})")
                            else:
                                print(f"[BACKGROUND] User {user.id} was already completed (concurrent update)")

                    except Exception as e:
                        print(f"[BACKGROUND] Error checking user {user.id}: {e}")
                        # Continue to next user on error
                        continue

            finally:
                db.close()

        except Exception as e:
            print(f"[BACKGROUND] Task error: {e}")
            import traceback
            traceback.print_exc()

        # Wait before next check
        await asyncio.sleep(PAYMENT_CHECK_INTERVAL)


async def start_background_tasks():
    """
    Start all background tasks.
    Returns the task handle for cleanup.
    """
    task = asyncio.create_task(check_pending_payments())
    return task
