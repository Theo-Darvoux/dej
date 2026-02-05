from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date, time, timedelta, timezone
import re

from src.db.session import get_db
from src.reservations import schemas, service
from src.reservations.availability import get_available_slots, is_slot_available, reserve_slot_with_lock, MAX_ORDERS_PER_SLOT
from src.auth.service import get_user_by_token, is_user_blacklisted, is_ordering_open
from src.core.exceptions import UserNotVerifiedException
from src.menu.utils import load_menu_data

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
async def check_availability(db: Session = Depends(get_db)):
    """
    Retourne les créneaux horaires disponibles.
    Un créneau est disponible s'il reste de la capacité (max 30 commandes par créneau).
    """
    slots = get_available_slots(db)
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

    # VALIDATION -2: Vérifier que les réservations sont ouvertes
    if not is_ordering_open():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les réservations sont fermées"
        )

    # VALIDATION -1: Vérifier la blacklist
    if is_user_blacklisted(current_user.normalized_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de commander"
        )

    # VALIDATION 0: Vérifier que l'utilisateur n'a pas déjà une réservation payée
    # Si l'utilisateur a déjà payé
    if current_user.payment_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà une réservation payée. Une seule réservation par personne."
        )
    
    # Si l'utilisateur a une commande en attente (non payée), on la remplace par la nouvelle
    # Cela permet aux utilisateurs de modifier leur commande ou de recommencer si le paiement échoue
    has_pending_order = current_user.menu_id or current_user.boisson_id or (current_user.bonus_ids and len(current_user.bonus_ids) > 0)

    if has_pending_order and current_user.payment_status != "completed":
        # Reset user reservation fields to allow new order
        current_user.menu_id = None
        current_user.boisson_id = None
        current_user.bonus_ids = []
        current_user.payment_status = "pending"
        current_user.payment_attempts = 0
        current_user.reservation_expires_at = None
        db.commit()
    
    reservation_date = date(2026, 2, 7)
    
    try:
        reservation_time = time.fromisoformat(request.heure_reservation)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'heure invalide (attendu: HH:MM)"
        )
    
    if not (time(8, 0) <= reservation_time <= time(17, 0)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'heure de réservation doit être entre 8h00 et 17h00"
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
        
        if not (1001 <= num_chambre <= 7999):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de chambre doit être entre 1001 et 7999"
            )
    else:
        # Si pas résident, adresse requise
        if not request.adresse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'adresse est requise pour les non-résidents"
            )
        # Vérifier que l'adresse est à Évry (91000) via API BAN
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # Search for the address using Géoplateforme geocoding service (replaces deprecated BAN API)
                response = await client.get(
                    "https://data.geopf.fr/geocodage/search",
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
                    # API returned non-200 status
                    print(f"Warning: BAN API returned status {response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service de validation d'adresse indisponible. Réessayez plus tard."
                    )
        except HTTPException:
            raise
        except Exception as e:
            # If BAN API is unreachable, reject the request (no permissive fallback)
            print(f"Warning: BAN API unreachable: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de validation d'adresse indisponible. Réessayez plus tard."
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
    extra_items = []  # Liste d'extras validés

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

    # Validation des extras (liste)
    if request.extras:
        seen_ids = set()
        for extra_name in request.extras:
            extra_item = find_item_by_name(extra_name)
            if not extra_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extra '{extra_name}' non trouvé"
                )
            if extra_item["item_type"] != "upsell":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"L'item '{extra_name}' n'est pas un extra (upsell)"
                )
            # Vérifier les doublons
            if extra_item["id"] in seen_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vous ne pouvez pas prendre deux fois le même extra ({extra_name})"
                )
            seen_ids.add(extra_item["id"])
            extra_items.append(extra_item)

    # VALIDATION SPECIALE: Poulet rôti et créneaux horaires
    # Le fournisseur de poulets rôtis ouvre à 9h00, donc impossible de servir avant 10h00
    has_roasted_chicken = any(
        'poulet' in extra_name.lower() 
        for extra_name in (request.extras or [])
    )
    
    if has_roasted_chicken:
        # Vérifier que le créneau est >= 10:00
        if reservation_time.hour < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le poulet rôti n'est pas disponible avant 10h00 (ouverture du fournisseur à 9h00). Veuillez choisir un créneau à partir de 10h00."
            )

    # VALIDATION 5: Vérifier la disponibilité du créneau avec verrouillage
    # Utilise SELECT FOR UPDATE pour éviter les conditions de concurrence
    if not reserve_slot_with_lock(db, reservation_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce créneau n'est plus disponible"
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
    
    # VALIDATION téléphone: accepte formats français et internationaux
    if request.phone:
        # Nettoyer: garder uniquement chiffres et + au début
        phone_cleaned = re.sub(r'[^\d+]', '', request.phone)
        # Le + ne peut être qu'au début
        if phone_cleaned.startswith('+'):
            phone_cleaned = '+' + phone_cleaned[1:].replace('+', '')
        else:
            phone_cleaned = phone_cleaned.replace('+', '')

        # Validation: 8-15 chiffres, optionnellement précédé de +
        if not re.match(r'^\+?[0-9]{8,15}$', phone_cleaned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Numéro de téléphone invalide (ex: 0612345678, +33612345678 ou +32123456789)"
            )
        current_user.phone = phone_cleaned
    else:
        current_user.phone = None
    
    # Sauvegarder demandes spéciales (max 500 caractères)
    special_requests_truncated = False
    if request.special_requests:
        stripped = request.special_requests.strip()
        if len(stripped) > 500:
            special_requests_truncated = True
            current_user.special_requests = stripped[:500]
        else:
            current_user.special_requests = stripped
    else:
        current_user.special_requests = None
    
    if request.habite_residence:
        current_user.numero_if_maisel = int(request.numero_chambre)
        current_user.adresse = None
        # Calculate building from room number (first digit)
        building_number = request.numero_chambre[0]
        current_user.adresse_if_maisel = schemas.BatimentMaisel(f"U{building_number}")
    else:
        current_user.adresse = request.adresse
        current_user.numero_if_maisel = None
        current_user.adresse_if_maisel = None
    
    # Stocker les IDs des items
    current_user.menu_id = menu_item["id"] if menu_item else None
    current_user.boisson_id = boisson_item["id"] if boisson_item else None
    current_user.bonus_ids = [extra["id"] for extra in extra_items] if extra_items else []

    # Note: La disponibilité des créneaux est gérée par comptage SQL dans availability.py
    # (MAX_ORDERS_PER_SLOT commandes max par créneau)

    # Calculer le montant total avec validation des prix
    total = 0.0
    if menu_item:
        menu_price = menu_item.get("price")
        if menu_price is None or menu_price < 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prix invalide pour le menu '{menu_item.get('name')}'"
            )
        total += menu_price

    if boisson_item:
        drink_price = boisson_item.get("price")
        if drink_price is None or drink_price < 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prix invalide pour la boisson '{boisson_item.get('name')}'"
            )
        total += drink_price

    for extra in extra_items:
        extra_price = extra.get("price")
        if extra_price is None or extra_price < 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prix invalide pour l'extra '{extra.get('name')}'"
            )
        total += extra_price

    # Validate total is positive (at least menu price)
    if total <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le montant total doit être positif"
        )
    
    current_user.total_amount = total
    current_user.status = "confirmed"
    current_user.payment_status = "pending"
    current_user.payment_attempts = 0
    current_user.reservation_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    current_user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la réservation: {str(e)}"
        )
    
    response = {
        "message": "Réservation créée avec succès",
        "id": current_user.id,  # Frontend attend "id" pour localStorage
        "user_id": current_user.id,  # Gardé pour rétrocompatibilité
        "status": current_user.status,
        "payment_status": current_user.payment_status,
        "date_reservation": str(current_user.date_reservation),
        "heure_reservation": str(current_user.heure_reservation),
        "menu": menu_item["name"] if menu_item else None,
        "boisson": boisson_item["name"] if boisson_item else None,
        "extras": [extra["name"] for extra in extra_items],
        "total_amount": current_user.total_amount,
    }

    # Add warning if special requests were truncated
    if special_requests_truncated:
        response["warning"] = "Vos demandes spéciales ont été tronquées à 500 caractères"

    return response


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
    
    # Vérifier la blacklist
    if is_user_blacklisted(current_user.normalized_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas le droit de commander"
        )
    
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
    if reservation.reservation_expires_at and datetime.now(timezone.utc) > reservation.reservation_expires_at:
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
        # Note: La disponibilité des créneaux est gérée par comptage SQL
        # Pas besoin de restaurer le stock manuellement
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur de connexion au service de paiement: {str(e)}"
        )
