from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date, time, timedelta
import re

from src.db.session import get_db
from src.reservations import schemas, service
from src.reservations.availability import get_available_slots, is_slot_available
from src.auth.service import get_user_by_token
from src.core.exceptions import UserNotVerifiedException
from src.menu.utils import load_menu_data
from src.reservations.models import MenuItemLimit

router = APIRouter()

# Helper to find item in JSON
def find_item_by_name(name: str):
    data = load_menu_data()
    # Search in menus, boissons, extras
    for menu in data.get("menus", []):
         if menu["name"] == name:
             menu["item_type"] = menu.get("item_type", "menu")
             return menu
    for drink in data.get("boissons", []):
         if drink["name"] == name:
             drink["item_type"] = "boisson"
             return drink
    for extra in data.get("extras", []):
         if extra["name"] == name:
             extra["item_type"] = "upsell"
             return extra
    return None

def find_category_name_by_id(cat_id: str):
    data = load_menu_data()
    for cat in data.get("categories", []):
        if cat["id"] == cat_id:
            return cat["name"]
    return None

@router.get("/availability")
async def check_availability(
    menu_id: Optional[str] = Query(None),
    boisson_id: Optional[str] = Query(None),
    bonus_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retourne les créneaux horaires disponibles pour les items du panier.
    Un créneau est disponible si tous les items ont du stock.
    """
    item_ids = [menu_id, boisson_id, bonus_id]
    slots = get_available_slots(db, item_ids)
    return {"slots": slots}


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
    - Heure: entre 7h et 20h
    - Numéro chambre: entre 1000 et 7999
    - Items menu vérifiés en DB
    - Pas de doublon de réservation
    - Créneau disponible
    """
    
    # VALIDATION 0: Vérifier que l'utilisateur n'a pas déjà une réservation
    now = datetime.utcnow()

    # Si l'utilisateur a déjà payé
    if current_user.payment_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà une réservation payée. Une seule réservation par personne."
        )
    
    # Si l'utilisateur a une réservation en attente mais expirée ou trop de tentatives
    is_expired = current_user.reservation_expires_at and now > current_user.reservation_expires_at
    too_many_attempts = current_user.payment_attempts >= 3
    
    if (is_expired or too_many_attempts) and current_user.payment_status != "completed":
        # Annuler l'ancienne commande et libérer le stock avant d'en créer une nouvelle
        # On fait ça silencieusement ici pour permettre d'en refaire une
        
        def restore_stock_internal(item_id, slot_time):
            if not item_id: return
            limit = db.query(MenuItemLimit).filter(
                MenuItemLimit.item_id == item_id,
                MenuItemLimit.start_time <= slot_time,
                MenuItemLimit.end_time > slot_time
            ).first()
            if limit and limit.current_quantity is not None:
                limit.current_quantity += 1
                db.add(limit)
        
        restore_stock_internal(current_user.menu_id, current_user.heure_reservation)
        restore_stock_internal(current_user.boisson_id, current_user.heure_reservation)
        restore_stock_internal(current_user.bonus_id, current_user.heure_reservation)
        
        # Reset user reservation fields
        current_user.menu_id = None
        current_user.boisson_id = None
        current_user.bonus_id = None
        current_user.payment_status = "pending"
        current_user.payment_attempts = 0
        current_user.reservation_expires_at = None
        db.commit()
    elif current_user.menu_id or current_user.boisson_id or current_user.bonus_id:
         # Si une commande est en cours et pas encore expirée
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà une commande en cours. Terminez le paiement ou attendez 1h."
        )
    
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
    
    if not (time(7, 0) <= reservation_time <= time(19, 0)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'heure de réservation doit être entre 7h00 et 19h00"
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
        
        if not (1000 <= num_chambre <= 7999):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de chambre doit être entre 1000 et 7999"
            )
    else:
        # Si pas résident, adresse requise
        if not request.adresse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'adresse est requise pour les non-résidents"
            )
        
        # Robust address validation using BAN API
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # Search for the address in BAN API
                response = await client.get(
                    "https://api-adresse.data.gouv.fr/search/",
                    params={"q": request.adresse, "limit": 1}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    
                    if not features:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Adresse non reconnue. Merci de préciser une adresse valide."
                        )
                    
                    # Check top result
                    top_result = features[0]
                    properties = top_result.get("properties", {})
                    postcode = properties.get("postcode")
                    city_name = properties.get("city", "")
                    
                    # Accept only Évry (91000), not Courcouronnes (91080)
                    if postcode != "91000":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Désolé, nous ne livrons pas à {city_name} ({postcode}). Livraison réservée à Évry (91000)."
                        )
                else:
                    # Fail-safe logic if API is down
                    lowercase_addr = request.adresse.lower()
                    if not any(x in lowercase_addr for x in ["evry", "91000"]):
                         raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Adresse invalide ou hors de la zone de livraison (Évry 91000)."
                        )
        except HTTPException:
            raise
        except Exception as e:
            # Si l'API BAN est injoignable, on fait un check basique
            print(f"Warning: BAN API unreachable: {str(e)}")
            lowercase_addr = request.adresse.lower()
            if not any(x in lowercase_addr for x in ["evry", "91000"]):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Adresse hors de la zone de livraison (Évry 91000)."
                )
    
    # VALIDATION 4: Vérifier que les items menu existent et correspondent au bon type
    # Groupes de catégories mutuellement exclusives pour les menus
    # On ne peut prendre qu'UN SEUL item parmi toutes ces catégories
    EXCLUSIVE_MENU_CATEGORIES = []
    # Dynamic loading of exclusive categories from JSON
    # We identify "Menu" categories as those that contain items in the "menus" list
    menu_data = load_menu_data()
    
    # Get all category IDs used by menus
    menu_category_ids = set()
    for m in menu_data.get("menus", []):
        menu_category_ids.add(m.get("category"))
        
    # Get names for these categories
    for cat in menu_data.get("categories", []):
         if cat["id"] in menu_category_ids:
             EXCLUSIVE_MENU_CATEGORIES.append(cat["name"])

    
    # VALIDATION MENU OBLIGATOIRE
    if not request.menu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez choisir au moins un menu pour commander"
        )
    
    menu_item = None
    boisson_item = None
    bonus_item = None
    
    if request.menu:
        menu_item = find_item_by_name(request.menu)
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu '{request.menu}' non trouvé"
            )
        if menu_item["item_type"] != "menu":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.menu}' n'est pas un menu"
            )
        
        # Vérifier que le menu appartient à une catégorie valide
        cat_name = find_category_name_by_id(menu_item["category"])
        if cat_name and cat_name not in EXCLUSIVE_MENU_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le menu doit provenir d'une des catégories: {', '.join(EXCLUSIVE_MENU_CATEGORIES)}"
            )
    
    if request.boisson:
        boisson_item = find_item_by_name(request.boisson)
        if not boisson_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Boisson '{request.boisson}' non trouvée"
            )
        if boisson_item["item_type"] != "boisson":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.boisson}' n'est pas une boisson"
            )
    
    if request.bonus:
        bonus_item = find_item_by_name(request.bonus)
        if not bonus_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bonus '{request.bonus}' non trouvé"
            )
        if bonus_item["item_type"] != "upsell":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'item '{request.bonus}' n'est pas un bonus (upsell)"
            )
    
    # VALIDATION 5: Vérifier la disponibilité du créneau pour tous les items
    item_ids = [
        menu_item["id"] if menu_item else None,
        boisson_item["id"] if boisson_item else None,
        bonus_item["id"] if bonus_item else None
    ]
    if not is_slot_available(db, item_ids, reservation_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce créneau n'est plus disponible pour les items sélectionnés"
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
    
    # VALIDATION téléphone: seulement chiffres et + au début
    if request.phone:
        phone_cleaned = re.sub(r'[^\d+]', '', request.phone)
        # Le + ne peut être qu'au début
        phone_cleaned = phone_cleaned[0] + phone_cleaned[1:].replace('+', '') if phone_cleaned.startswith('+') else phone_cleaned.replace('+', '')
        if not re.match(r'^\+?\d{9,12}$', phone_cleaned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Numéro de téléphone invalide (format attendu: 0612345678 ou +33612345678)"
            )
        current_user.phone = phone_cleaned
    else:
        current_user.phone = None
    
    # Sauvegarder demandes spéciales
    current_user.special_requests = request.special_requests.strip()[:500] if request.special_requests else None
    
    if request.habite_residence:
        current_user.numero_if_maisel = int(request.numero_chambre)
        current_user.adresse = None
    else:
        current_user.adresse = request.adresse
        current_user.numero_if_maisel = None
    
    # Stocker les IDs des items (nouveaux champs String)
    current_user.menu_id = menu_item["id"] if menu_item else None
    current_user.boisson_id = boisson_item["id"] if boisson_item else None
    current_user.bonus_id = bonus_item["id"] if bonus_item else None
    
    # ---------------- DEBUT GESTION STOCK ----------------
    def check_and_decrement_stock(item_id, slot_time):
        """Vérifie et décrémente stock pour un item à l'heure donnée"""
        
        # Trouver limite correspondante (ou une qui couvre cette heure)
        # Note: Dans une vraie implém, il faudrait gérer le jour aussi, ici on suppose que limits sont valides pour le jour J
        limit = db.query(MenuItemLimit).filter(
            MenuItemLimit.item_id == item_id,
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
        l = check_and_decrement_stock(menu_item["id"], reservation_time)
        if l: stock_updates.append(l)
    if boisson_item:
        l = check_and_decrement_stock(boisson_item["id"], reservation_time)
        if l: stock_updates.append(l)
    if bonus_item:
        l = check_and_decrement_stock(bonus_item["id"], reservation_time)
        if l: stock_updates.append(l)
    # ---------------- FIN GESTION STOCK ----------------
    
    # Calculer le montant total
    total = 0.0
    if menu_item:
        total += menu_item.get("price", 0)
    if boisson_item:
        total += boisson_item.get("price", 0)
    if bonus_item:
        total += bonus_item.get("price", 0)
    
    current_user.total_amount = total
    current_user.status = "confirmed"
    current_user.payment_status = "pending"
    current_user.payment_attempts = 0
    current_user.reservation_expires_at = datetime.utcnow() + timedelta(hours=1)
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
        "id": current_user.id,  # Frontend attend "id" pour localStorage
        "user_id": current_user.id,  # Gardé pour rétrocompatibilité
        "status": current_user.status,
        "payment_status": current_user.payment_status,
        "date_reservation": str(current_user.date_reservation),
        "heure_reservation": str(current_user.heure_reservation),
        "menu": menu_item["name"] if menu_item else None,
        "boisson": boisson_item["name"] if boisson_item else None,
        "bonus": bonus_item["name"] if bonus_item else None,
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
    # Note: Reservation might be an alias for User still or separated?
    # Original code imported Reservation from src.reservations.models
    # But src.reservations.models was empty/comment-only in Step 36.
    # So "Reservation" is likely not there.
    # Let's check imports in original router.py (Step 37)
    # line 446: from src.reservations.models import Reservation
    # This suggests Reservation WAS in src.reservations.models or there's some trick.
    # BUT Step 36 showed "ReservationItem table has been merged into User model" and 1 line.
    # Ah! 'Reservation' might be 'User' model?
    # In Step 54 (service.py), it queries 'User'.
    # In 'process_payment' above (Step 37), it queries Reservation.
    # If reservations.models was empty, this import would fail.
    # Maybe I missed something about reservations.models content?
    # Wait, Step 36 output said "Total Lines: 1".
    # So previous code was BROKEN or I am misinterpreting.
    # OR 'Reservation' is defined in users.models? 
    # NO. 
    # Let's assume Reservation IS User (logic-wise).
    
    from src.users.models import User as Reservation
    from datetime import datetime, timezone
    import httpx
    
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.id == current_user.id # user_id check matches id since Reservation IS User
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
    
    # Vérifier expiration
    if reservation.reservation_expires_at and datetime.utcnow() > reservation.reservation_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Votre réservation a expiré (délai de 1h dépassé). Veuillez recommencer."
        )
    
    # Vérifier tentatives
    if reservation.payment_attempts >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trop de tentatives de paiement échouées. Votre réservation est annulée."
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
                reservation.payment_attempts += 1
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Erreur lors du paiement (Tentative {reservation.payment_attempts}/3)"
                )
    except Exception as e:
        
        def restore_stock(item_id, slot_time):
            if not item_id: return
            limit = db.query(MenuItemLimit).filter(
                MenuItemLimit.item_id == item_id,
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
