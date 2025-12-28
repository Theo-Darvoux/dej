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
    Étape 3: Création de la réservation
    - L'utilisateur doit être authentifié (cookie)
    - Email vérifié et cotisant BDE
    - Rentre les infos du formulaire (date, heure, chambre/adresse)
    """
    reservation = service.create_reservation(
        user_id=current_user.id,
        date_reservation=request.date_reservation,
        heure_reservation=request.heure_reservation,
        habite_residence=request.habite_residence,
        numero_chambre=request.numero_chambre,
        numero_immeuble=request.numero_immeuble,
        adresse=request.adresse,
        db=db
    )
    
    return schemas.ReservationResponse.model_validate(reservation)


@router.post("/{reservation_id}/payment-intent", response_model=schemas.PaymentIntentResponse)
async def create_payment_intent(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Étape 4: Créer un intent de paiement HelloAsso
    - Vérifie que la réservation existe et appartient à l'utilisateur
    - Appelle HelloAsso pour créer le paiement
    - Retourne l'URL de redirection
    
    TODO: À implémenter avec la doc HelloAsso
    """
    from reservations.models import Reservation
    
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
    
    # TODO: Implémenter appel HelloAsso avec la doc
    # Pour l'instant, retour mock
    return schemas.PaymentIntentResponse(
        intent_id="MOCK_INTENT_ID",
        redirect_url="https://helloasso.com/checkout/mock"
    )


@router.post("/{reservation_id}/payment-confirm", response_model=schemas.PaymentConfirmResponse)
async def confirm_payment(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Étape 5: Page de validation après paiement
    - Webhook ou retour HelloAsso met à jour payment_status
    - Cette route récupère juste le statut pour affichage
    
    TODO: À implémenter avec la doc HelloAsso (webhooks)
    """
    from reservations.models import Reservation
    from datetime import datetime
    
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.user_id == current_user.id
    ).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation non trouvée"
        )
    
    # TODO: Implémenter vérification HelloAsso
    # Pour l'instant, mock: marquer comme payé
    if reservation.payment_status == "pending":
        reservation.payment_status = "completed"
        reservation.payment_date = datetime.now(datetime.timezone.utc)
        db.commit()
    
    return schemas.PaymentConfirmResponse(
        message="Paiement confirmé",
        reservation_id=reservation.id,
        payment_status=reservation.payment_status
    )
