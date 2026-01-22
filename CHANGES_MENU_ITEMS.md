# Modifications - Système de Réservation avec Items de Menu

## Résumé des changements

Les modifications permettent maintenant de stocker les informations de réservation avec des références aux items de menu (ForeignKey) au lieu de simples chaînes de caractères.

## Backend

### 1. Modèle User (`backend/src/users/models.py`)
- ✅ Remplacé les colonnes `menu`, `boisson`, `bonus` (String) par `menu_id`, `boisson_id`, `bonus_id` (ForeignKey vers MenuItem)
- ✅ Ajouté les relations SQLAlchemy : `menu_item`, `boisson_item`, `bonus_item`

### 2. Migration de base de données (`backend/migration/versions/001_change_menu_fields_to_foreign_keys.py`)
- ✅ Créé une migration Alembic pour transformer les colonnes String en ForeignKey
- ✅ Ajout de contraintes de clé étrangère avec `ondelete='SET NULL'`

### 3. Schemas (`backend/src/users/schemas.py`)
- ✅ `ReservationData` : Schema pour recevoir les données de réservation avec validation
  - Validation des IDs positifs pour menu_id, boisson_id, bonus_id
  - Validation du numéro de téléphone (min 10 caractères)
- ✅ `MenuItemResponse` : Schema pour retourner les détails d'un MenuItem
- ✅ `UserWithReservationResponse` : Schema complet avec relations

### 4. Router (`backend/src/users/router.py`)
- ✅ Endpoint `POST /api/users/reservation` : Enregistre une réservation
  - Vérifie que les menu_items existent
  - Vérifie que le type correspond (menu, boisson, bonus)
  - Calcule le montant total automatiquement
  - Met à jour l'utilisateur connecté
- ✅ Endpoint `GET /api/users/me` : Récupère les détails complets de l'utilisateur

## Frontend

### 5. App.tsx (`frontend/src/App.tsx`)
- ✅ Ajout du type `ReservationData` pour typer les données
- ✅ États pour stocker les IDs des items sélectionnés : `menuId`, `boissonId`, `bonusId`
- ✅ État `reservationData` pour stocker toutes les infos de réservation
- ✅ Modification de `handleAddToCart` pour capturer les IDs selon le type d'item
- ✅ Transmission des données aux popups enfants

### 6. AptPopup (`frontend/src/components/popup/3apartment/AptPopup.tsx`)
- ✅ Nouveau type `ApartmentData` pour les données d'appartement
- ✅ Gestion de l'état `habiteResidence` (radio buttons)
- ✅ Callback `onContinue(data)` qui remonte les données au parent
- ✅ Affichage conditionnel : code appartement OU adresse complète

### 7. InfoPopup (`frontend/src/components/popup/info/InfoPopup.tsx`)
- ✅ Ajout de champs pour date et heure de réservation
- ✅ Nouvelle prop `onReservationDataChange` pour remonter les données
- ✅ Nouvelle prop `reservationData` pour recevoir les IDs menu/boisson/bonus
- ✅ Envoi de la requête POST `/api/users/reservation` avant le paiement
- ✅ Gestion des erreurs avec messages clairs

## API Endpoints

### POST /api/users/reservation
```json
{
  "date_reservation": "2026-01-15",
  "heure_reservation": "19:30",
  "habite_residence": true,
  "numero_chambre": "1234",
  "phone": "0612345678",
  "menu_id": 1,
  "boisson_id": 5,
  "bonus_id": 8
}
```

**Validations automatiques :**
- ✅ Vérifie que l'utilisateur est connecté (cookie)
- ✅ Vérifie que les menu_items existent en DB
- ✅ Vérifie que le type de l'item correspond (menu/boisson/bonus)
- ✅ Calcule automatiquement le montant total
- ✅ Valide le format de date (YYYY-MM-DD) et heure (HH:MM)

### GET /api/users/me
Retourne les détails complets de l'utilisateur avec les items de menu populés.

## Migration de la base de données

Pour appliquer la migration :

```bash
cd backend
alembic upgrade head
```

Ou si vous utilisez Docker :
```bash
docker-compose exec backend alembic upgrade head
```

## Tests recommandés

1. ✅ Sélectionner un menu, une boisson et un bonus
2. ✅ Passer par les popups et vérifier que les données sont bien stockées
3. ✅ Vérifier que les IDs sont bien envoyés dans la requête
4. ✅ Tester avec des IDs invalides pour voir les erreurs
5. ✅ Vérifier que le montant total est calculé correctement
6. ✅ Tester avec habite_residence = true et false

## Notes importantes

- Les relations utilisent `foreign_keys=[]` car il y a plusieurs ForeignKey vers la même table (MenuItem)
- Les contraintes sont en `SET NULL` pour ne pas bloquer si un MenuItem est supprimé
- Le frontend valide côté client, mais le backend re-valide tout pour la sécurité
- Les prix sont stockés en Float dans la DB mais affichés avec 2 décimales
