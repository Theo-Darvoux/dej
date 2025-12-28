# 💳 HelloAsso Integration - TODO

## Ce qui est prêt

Le backend a des **placeholders** pour HelloAsso dans:

1. **core/payment.py** - Client HelloAsso avec méthodes à implémenter
2. **reservations/router.py** - Endpoints paiement (retournent mocks pour l'instant)
3. **core/config.py** - Variables env HelloAsso

## Ce qui manque (en attente de la doc)

### 1. Authentification HelloAsso

**À définir:**
- Type d'auth (OAuth2, API key, autre ?)
- Où stocker les credentials (env vars ?)
- Refresh tokens si nécessaire

**Fichier à modifier:** `core/payment.py`

```python
class HelloAssoClient:
    async def authenticate(self):
        # TODO avec doc
        pass
```

---

### 2. Création d'un paiement

**À définir:**
- Endpoint exact (POST /checkout, /payments, autre ?)
- Format du payload (montant, devise, metadata, etc.)
- Réponse attendue (intent_id, checkout_url, etc.)

**Fichier à modifier:** `core/payment.py`

```python
async def create_payment_intent(
    self,
    amount: float,
    reservation_id: int,
    user_email: str
) -> dict:
    # TODO: Appel API HelloAsso
    # POST https://api.helloasso.com/v5/...
    # Headers: Authorization, Content-Type
    # Body: {...}
    # Return: {intent_id, redirect_url}
    pass
```

**Fichier à modifier:** `reservations/router.py` (ligne ~140)

```python
@router.post("/{reservation_id}/payment-intent")
async def create_payment_intent(...):
    # Remplacer le mock par:
    from core.payment import helloasso_client
    
    result = await helloasso_client.create_payment_intent(
        amount=10.0,  # À définir selon réservation
        reservation_id=reservation_id,
        user_email=current_user.email
    )
    
    # Stocker intent_id dans la réservation
    reservation.payment_intent_id = result["intent_id"]
    db.commit()
    
    return schemas.PaymentIntentResponse(
        intent_id=result["intent_id"],
        redirect_url=result["redirect_url"]
    )
```

---

### 3. Webhooks HelloAsso

**À définir:**
- URL webhook à configurer
- Format du payload reçu
- Signature/sécurité (HMAC, autre ?)
- Événements supportés (payment.succeeded, payment.failed, etc.)

**Fichier à créer:** `webhooks/helloasso.py`

```python
from fastapi import APIRouter, Request, HTTPException
from core.payment import helloasso_client

router = APIRouter()

@router.post("/webhooks/helloasso")
async def helloasso_webhook(request: Request):
    # TODO: Vérifier signature
    payload = await request.json()
    
    # TODO: Extraire event type
    event_type = payload.get("type")
    
    if event_type == "payment.succeeded":
        intent_id = payload.get("intent_id")
        
        # Trouver la réservation
        from reservations.models import Reservation
        from db.session import SessionLocal
        from datetime import datetime
        
        db = SessionLocal()
        reservation = db.query(Reservation).filter(
            Reservation.payment_intent_id == intent_id
        ).first()
        
        if reservation:
            reservation.payment_status = "completed"
            reservation.payment_date = datetime.now(datetime.timezone.utc)
            db.commit()
    
    elif event_type == "payment.failed":
        # TODO: Gérer échec
        pass
    
    return {"status": "ok"}
```

**À ajouter dans main.py:**

```python
from webhooks.helloasso import router as helloasso_webhook_router

app.include_router(helloasso_webhook_router)
```

---

### 4. Vérification statut paiement

**À définir:**
- Endpoint API pour vérifier statut (GET /payments/{id} ?)
- Format de réponse

**Fichier à modifier:** `core/payment.py`

```python
async def verify_payment(self, intent_id: str) -> dict:
    # TODO: Appel API HelloAsso
    # GET https://api.helloasso.com/v5/payments/{intent_id}
    # Return: {status, amount, date, etc.}
    pass
```

**Fichier à modifier:** `reservations/router.py` (ligne ~180)

```python
@router.post("/{reservation_id}/payment-confirm")
async def confirm_payment(...):
    # Remplacer le mock par:
    from core.payment import helloasso_client
    
    payment = await helloasso_client.verify_payment(
        reservation.payment_intent_id
    )
    
    if payment["status"] == "succeeded":
        reservation.payment_status = "completed"
        reservation.payment_date = datetime.now(datetime.timezone.utc)
        db.commit()
    
    return schemas.PaymentConfirmResponse(...)
```

---

## Configuration nécessaire

### Variables d'environnement

À ajouter dans `.env`:

```bash
# HelloAsso
HELLOASSO_API_KEY=votre_cle_api
HELLOASSO_API_SECRET=votre_secret  # Si OAuth2
HELLOASSO_WEBHOOK_SECRET=secret_signature  # Si webhooks signés
HELLOASSO_ORGANIZATION_SLUG=mc-int  # Votre organisation
```

### Montants

Définir les prix dans `core/config.py`:

```python
class Settings(BaseSettings):
    # ...
    RESERVATION_PRICE: float = 10.0  # Prix en euros
```

---

## Checklist d'implémentation

Quand vous aurez la doc HelloAsso:

- [ ] Lire la doc complète
- [ ] Créer compte/organisation HelloAsso
- [ ] Obtenir les credentials API
- [ ] Implémenter `core/payment.py`:
  - [ ] Authentification
  - [ ] create_payment_intent()
  - [ ] verify_payment()
  - [ ] handle_webhook()
- [ ] Mettre à jour `reservations/router.py`:
  - [ ] Endpoint payment-intent (remplacer mock)
  - [ ] Endpoint payment-confirm (remplacer mock)
- [ ] Créer `webhooks/helloasso.py`
- [ ] Configurer URL webhook sur HelloAsso
- [ ] Tester en sandbox/dev
- [ ] Gérer les erreurs (timeout, failed payment, etc.)
- [ ] Logger les transactions
- [ ] Tests unitaires

---

## Questions à poser à HelloAsso

1. **Authentification**: OAuth2 ou API key simple ?
2. **Sandbox**: Existe-t-il un environnement de test ?
3. **Webhooks**: Format exact du payload et signature
4. **Montants**: Devise supportée (EUR uniquement ?)
5. **Frais**: Qui paye les frais HelloAsso ?
6. **Remboursements**: API pour gérer les annulations/remboursements ?
7. **Rate limiting**: Limites d'appels API ?

---

## Ressources

Une fois la doc reçue, ajouter ici:
- Lien vers doc API HelloAsso
- Exemples de payloads
- Dashboard HelloAsso
- Support technique
