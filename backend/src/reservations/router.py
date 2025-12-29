from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from typing import Optional, List

from src.db.session import get_db
from src.reservations import schemas, service
from src.auth.service import get_user_by_token
from src.core.exceptions import UserNotVerifiedException

router = APIRouter()


def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Dépendance pour récupérer l'utilisateur depuis le cookie access_token.
    Protège les routes qui nécessitent une authentification.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non connecté"
        )
    
    user = get_user_by_token(access_token, db)
    return user


@router.post("/", response_model=schemas.ReservationResponse)
async def create_reservation(
    request: schemas.ReservationCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Étape 3: Création de la réservation avec items menu
    - L'utilisateur doit être authentifié (cookie)
    - Email vérifié et cotisant BDE
    - Rentre les infos du formulaire + items du panier
    """
    # Convertir items en dict pour le service
    items_data = [item.model_dump() for item in request.items] if request.items else []
    
    reservation = service.create_reservation(
        user_id=current_user.id,
        date_reservation=request.date_reservation,
        heure_reservation=request.heure_reservation,
        habite_residence=request.habite_residence,
        numero_chambre=request.numero_chambre,
        numero_immeuble=request.numero_immeuble,
        adresse=request.adresse,
        phone=request.phone,
        items=items_data,
        db=db
    )
    
    return schemas.ReservationResponse.model_validate(reservation)


@router.post("/{reservation_id}/payment", response_model=schemas.PaymentConfirmResponse)
async def process_payment(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Étape 4: Traiter le paiement via Stripe Mock
    - Vérifie que la réservation existe et appartient à l'utilisateur
    - Appelle Stripe Mock pour créer le payment intent
    - Met à jour le payment_status
    """
    from src.reservations.models import Reservation
    from datetime import datetime, timezone
    import httpx
    
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.user_id == current_user.id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation non trouvée"
        )
    
    if reservation.payment_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paiement déjà effectué"
        )
    
    # Appeler Stripe Mock
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://stripe-mock:12111/v1/payment_intents",
                data={
                    "amount": int(reservation.total_amount * 100),  # Convertir en centimes
                    "currency": "eur",
                    "payment_method_types[]": "card"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                reservation.payment_status = "completed"
                reservation.payment_intent_id = payment_data.get("id", "STRIPE_MOCK_INTENT")
                reservation.payment_date = datetime.now(timezone.utc)
                db.commit()
                
                return schemas.PaymentConfirmResponse(
                    message="Paiement confirmé",
                    reservation_id=reservation.id,
                    payment_status=reservation.payment_status
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Erreur lors du paiement"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur de connexion au service de paiement: {str(e)}"
        )
