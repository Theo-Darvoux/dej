from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, time

from src.db.session import get_db
from src.reservations import schemas, service
from src.auth.service import get_user_by_token
from src.core.exceptions import UserNotVerifiedException
from src.menu.models import MenuItem

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


@router.post("/", response_model=dict)
async def create_reservation(
    request: schemas.ReservationCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
):
    """
    Étape 3: Création de la réservation avec validations strictes
    - Date: 7 février 2026
    - Heure: entre 7h et 18h
    - Numéro chambre: entre 1000 et 6999
    - Items menu vérifiés en DB
    """
    
    # VALIDATION 1: Date de réservation doit être le 7 février 2026
    try:
        reservation_date = date.fromisoformat(request.date_reservation)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de date invalide (attendu: YYYY-MM-DD)"
        )
    
    if reservation_date != date(2026, 2, 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La réservation doit être pour le 7 février 2026"
        )
    
    # VALIDATION 2: Heure de réservation entre 7h et 18h, par tranches de 1h (minutes = 00)
    try:
        reservation_time = time.fromisoformat(request.heure_reservation)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'heure invalide (attendu: HH:MM)"
        )
    
    if not (time(7, 0) <= reservation_time <= time(18, 0)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'heure de réservation doit être entre 7h00 et 18h00"
        )
    # Tranche d'1h: minutes doivent être 00
    if reservation_time.minute != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'heure doit être sélectionnée par tranches d'1h (minutes = 00)"
        )
    
    # VALIDATION 3: Numéro de chambre si habite résidence
    if request.habite_residence:
        if not request.numero_chambre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de chambre est requis pour les résidents"
            )
        
        try:
            num_chambre = int(request.numero_chambre)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de chambre doit être un nombre"
            )
        
        if not (1000 <= num_chambre <= 6999):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de chambre doit être entre 1000 et 6999"
            )
    else:
        # Si pas résident, adresse requise
        if not request.adresse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'adresse est requise pour les non-résidents"
            )
    
    # VALIDATION 4: Vérifier que les items menu existent et correspondent au bon type
    menu_item = None
    boisson_item = None
    bonus_item = None
    
    if request.menu:
        menu_item = db.query(MenuItem).filter(MenuItem.name == request.menu).first()
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu '{request.menu}' non trouvé"
            )
        if menu_item.item_type != "menu":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.menu}' n'est pas un menu"
            )
    
    if request.boisson:
        boisson_item = db.query(MenuItem).filter(MenuItem.name == request.boisson).first()
        if not boisson_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Boisson '{request.boisson}' non trouvée"
            )
        if boisson_item.item_type != "boisson":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.boisson}' n'est pas une boisson"
            )
    
    if request.bonus:
        bonus_item = db.query(MenuItem).filter(MenuItem.name == request.bonus).first()
        if not bonus_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bonus '{request.bonus}' non trouvé"
            )
        if bonus_item.item_type != "bonus":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.bonus}' n'est pas un bonus"
            )
    
    # Vérification que l'utilisateur est bien vérifié et cotisant
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié"
        )
    
    if not current_user.is_cotisant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas cotisant BDE actif"
        )
    
    # Mettre à jour l'utilisateur avec les données validées
    current_user.date_reservation = reservation_date
    current_user.heure_reservation = reservation_time
    current_user.habite_residence = request.habite_residence
    current_user.phone = request.phone
    
    if request.habite_residence:
        current_user.numero_if_maisel = int(request.numero_chambre)
        current_user.adresse = None
    else:
        current_user.adresse = request.adresse
        current_user.numero_if_maisel = None
    
    # Stocker les IDs des items (nouveaux champs ForeignKey)
    current_user.menu_id = menu_item.id if menu_item else None
    current_user.boisson_id = boisson_item.id if boisson_item else None
    current_user.bonus_id = bonus_item.id if bonus_item else None
    
    # ---------------- DEBUT GESTION STOCK ----------------
    def check_and_decrement_stock(item_id, slot_time):
        """Vérifie et décrémente stock pour un item à l'heure donnée"""
        from src.menu.models import MenuItemLimit
        
        # Trouver limite correspondante (ou une qui couvre cette heure)
        # Note: Dans une vraie implém, il faudrait gérer le jour aussi, ici on suppose que limits sont valides pour le jour J
        limit = db.query(MenuItemLimit).filter(
            MenuItemLimit.menu_item_id == item_id,
            MenuItemLimit.start_time <= slot_time,
            MenuItemLimit.end_time > slot_time
        ).first()
        
        if limit:
            if limit.current_quantity is not None:
                if limit.current_quantity <= 0:
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Item ID {item_id} n'est plus disponible pour ce créneau ({slot_time})"
                    )
                limit.current_quantity -= 1
                db.add(limit) # Mark as modified
                return limit
        return None

    stock_updates = []
    if menu_item:
        l = check_and_decrement_stock(menu_item.id, reservation_time)
        if l: stock_updates.append(l)
    if boisson_item:
        l = check_and_decrement_stock(boisson_item.id, reservation_time)
        if l: stock_updates.append(l)
    if bonus_item:
        l = check_and_decrement_stock(bonus_item.id, reservation_time)
        if l: stock_updates.append(l)
    # ---------------- FIN GESTION STOCK ----------------
    
    # Calculer le montant total
    total = 0.0
    if menu_item:
        total += menu_item.price
    if boisson_item:
        total += boisson_item.price
    if bonus_item:
        total += bonus_item.price
    
    current_user.total_amount = total
    current_user.status = "confirmed"
    current_user.payment_status = "pending"
    current_user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la réservation: {str(e)}"
        )
    
    return {
        "message": "Réservation créée avec succès",
        "user_id": current_user.id,
        "status": current_user.status,
        "payment_status": current_user.payment_status,
        "date_reservation": str(current_user.date_reservation),
        "heure_reservation": str(current_user.heure_reservation),
        "menu": menu_item.name if menu_item else None,
        "boisson": boisson_item.name if boisson_item else None,
        "bonus": bonus_item.name if bonus_item else None,
        "total_amount": current_user.total_amount,
    }


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
        # Restoration du stock en cas d'échec critique (optionnel selon specs, mais demandé par user)
        # Ici on re-crédite si le paiement plante VRAIMENT (exception technique ou 502)
        # Pour un simple "refus de carte", on pourrait garder la résa en "pending" et laisser user réessayer.
        # Mais le user a dit "si le paiement echoue alors la on readdition".
        # On va simplifier : Si exception technique => restore.
        
        # NOTE: Pour restaurer proprement, il faudrait retrouver les limits impactées.
        # On va le faire basiquement pour "reservation.heure_reservation"
        
        from src.menu.models import MenuItemLimit
        def restore_stock(item_id, slot_time):
            if not item_id: return
            limit = db.query(MenuItemLimit).filter(
                MenuItemLimit.menu_item_id == item_id,
                MenuItemLimit.start_time <= slot_time,
                MenuItemLimit.end_time > slot_time
            ).first()
            if limit and limit.current_quantity is not None:
                limit.current_quantity += 1
                db.add(limit)

        try:
             restore_stock(reservation.menu_id, reservation.heure_reservation)
             restore_stock(reservation.boisson_id, reservation.heure_reservation)
             restore_stock(reservation.bonus_id, reservation.heure_reservation)
             db.commit()
        except:
             pass # Fail safe

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur de connexion au service de paiement: {str(e)}"
        )
