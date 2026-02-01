"""
Module de gestion des disponibilités des créneaux horaires.

Optimized to use efficient database queries instead of N+1 pattern.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import time
from typing import Dict

from src.users.models import User


# ============================================================
# CONFIGURATION - Modifier cette valeur pour changer la limite
# ============================================================
MAX_ORDERS_PER_SLOT = 30  # Nombre maximum de commandes par créneau
# ============================================================


# Créneaux horaires disponibles (8h-9h à 17h-18h)
TIME_SLOTS = [
    {"slot": "08:00 - 09:00", "start": time(8, 0), "end": time(9, 0)},
    {"slot": "09:00 - 10:00", "start": time(9, 0), "end": time(10, 0)},
    {"slot": "10:00 - 11:00", "start": time(10, 0), "end": time(11, 0)},
    {"slot": "11:00 - 12:00", "start": time(11, 0), "end": time(12, 0)},
    {"slot": "12:00 - 13:00", "start": time(12, 0), "end": time(13, 0)},
    {"slot": "13:00 - 14:00", "start": time(13, 0), "end": time(14, 0)},
    {"slot": "14:00 - 15:00", "start": time(14, 0), "end": time(15, 0)},
    {"slot": "15:00 - 16:00", "start": time(15, 0), "end": time(16, 0)},
    {"slot": "16:00 - 17:00", "start": time(16, 0), "end": time(17, 0)},
    {"slot": "17:00 - 18:00", "start": time(17, 0), "end": time(18, 0)},
]


def get_all_slot_counts(db: Session) -> Dict[time, int]:
    """
    Get reservation counts for all time slots in a single query.

    Returns:
        Dictionary mapping slot start time to reservation count
    """
    # Single query with GROUP BY to get all counts at once
    counts = db.query(
        User.heure_reservation,
        func.count(User.id).label('count')
    ).filter(
        User.menu_id.isnot(None),
        User.payment_status.in_(["completed", "pending"]),
        User.heure_reservation.isnot(None)
    ).group_by(User.heure_reservation).all()

    # Convert to dictionary
    return {row.heure_reservation: row.count for row in counts}


def count_reservations_for_slot(db: Session, slot_time: time) -> int:
    """
    Compte le nombre de réservations confirmées pour un créneau donné.

    On compte les utilisateurs qui ont:
    - Une heure de réservation correspondant au créneau
    - Un statut de paiement 'completed' OU 'pending' (réservation en cours)
    - Un menu_id non null (donc une commande en cours)
    """
    count = db.query(func.count(User.id)).filter(
        User.heure_reservation == slot_time,
        User.menu_id.isnot(None),
        User.payment_status.in_(["completed", "pending"])
    ).scalar()

    return count or 0


def get_available_slots(db: Session) -> list[dict]:
    """
    Retourne les créneaux avec leur disponibilité basée sur le nombre de commandes.

    Optimized to use a single GROUP BY query instead of N sequential queries.

    Args:
        db: Session SQLAlchemy

    Returns:
        Liste de créneaux avec leur disponibilité:
        [
            {
                "slot": "08:00 - 09:00",
                "start": "08:00",
                "available": True,
                "current_count": 12,
                "max_capacity": 30
            },
            ...
        ]
    """
    # Get all counts in a single query
    slot_counts = get_all_slot_counts(db)

    result = []
    for slot in TIME_SLOTS:
        current_count = slot_counts.get(slot["start"], 0)
        remaining = MAX_ORDERS_PER_SLOT - current_count

        result.append({
            "slot": slot["slot"],
            "start": slot["start"].strftime("%H:%M"),
            "available": remaining > 0,
            "current_count": current_count,
            "max_capacity": MAX_ORDERS_PER_SLOT
        })

    return result


def is_slot_available(db: Session, slot_time: time) -> bool:
    """
    Vérifie si un créneau spécifique est disponible.

    Args:
        db: Session SQLAlchemy
        slot_time: L'heure du créneau (ex: time(8, 0) pour 8h)

    Returns:
        True si disponible, False sinon
    """
    current_count = count_reservations_for_slot(db, slot_time)
    return current_count < MAX_ORDERS_PER_SLOT


def reserve_slot_with_lock(db: Session, slot_time: time) -> bool:
    """
    Atomically check slot availability with row-level locking to prevent race conditions.

    Uses SELECT FOR UPDATE to lock rows while checking availability, preventing
    two concurrent requests from overbooking the same time slot.

    Args:
        db: Session SQLAlchemy
        slot_time: L'heure du créneau (ex: time(8, 0) pour 8h)

    Returns:
        True si le créneau est disponible et peut être réservé, False sinon
    """
    from sqlalchemy import text

    # Lock rows for this time slot and count them
    # FOR UPDATE cannot be used with COUNT(*), so we select IDs and count in Python
    result = db.execute(
        text("""
            SELECT id FROM users
            WHERE heure_reservation = :slot_time
            AND menu_id IS NOT NULL
            AND payment_status IN ('completed', 'pending')
            FOR UPDATE
        """),
        {"slot_time": slot_time}
    ).fetchall()

    current_count = len(result) if result else 0
    return current_count < MAX_ORDERS_PER_SLOT
