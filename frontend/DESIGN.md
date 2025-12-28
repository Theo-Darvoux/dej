# MC INT - Frontend Modern Design

## 🎨 Design Features

Le frontend a été créé avec un **design McDonald's moderne** inspiré du style de **Monks** avec:

### Caractéristiques visuelles:
- **Couleurs McDonald's**: Rouge vif (#dc143c), jaune (#ffc72c), orange (#ff6b35)
- **Gradients fluidement animés**: Dégradés rouges → rose → violet comme Monks
- **Blobs animés**: Formes organiques flottantes en arrière-plan (effet Monks)
- **Animations fluides**: 
  - Fade In Up (apparition)
  - Slide In Right (glissement)
  - Hover effects (effets au survol)
  - Blob animations (mouvements organiques)

### Pages créées:
1. **Login** - Authentification par email
2. **Verify** - Vérification du code 6 chiffres
3. **Reservation** - Création de réservation
4. **Dashboard** - Gestion des réservations

## 🚀 Installation & Démarrage

### Prérequis
- Node.js 18+
- Angular 20.3.0
- npm

### Installation
```bash
cd frontend
npm install
```

### Développement
```bash
npm start
```
L'app sera disponible à `http://localhost:4200`

### Build Production
```bash
npm run build
```

## 📁 Structure du projet

```
frontend/
├── src/
│   ├── app/
│   │   ├── pages/
│   │   │   ├── login/          # Page de connexion
│   │   │   ├── verify/         # Page de vérification
│   │   │   ├── reservation/    # Page de réservation
│   │   │   └── dashboard/      # Page de tableau de bord
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   └── reservation.service.ts
│   │   ├── guards/
│   │   │   └── auth.guard.ts
│   │   ├── app.ts
│   │   ├── app.routes.ts
│   │   ├── app.config.ts
│   │   └── app.scss
│   ├── styles.scss
│   └── index.html
└── package.json
```

## 🔌 Intégration Backend

L'application se connecte à l'API backend via:
- **URL**: `/api`
- **CORS**: Configuré pour `localhost:4200` et variables d'environnement

### Endpoints utilisés:
- `POST /api/auth/request-code` - Demande d'envoi de code
- `POST /api/auth/verify` - Vérification du code
- `POST /api/reservations/` - Création de réservation
- `GET /api/reservations/my` - Récupération des réservations
- `DELETE /api/reservations/{id}` - Annulation de réservation

## 🎯 Flux d'utilisation

1. **Login** → Entrer l'email
2. **Verify** → Vérifier le code reçu
3. **Reservation** → Remplir le formulaire de réservation
4. **Dashboard** → Voir toutes les réservations et payer

## 🎨 Système de design

### Couleurs
- **Primaire**: #dc143c (Rouge McDonald's)
- **Secondaire**: #ffc72c (Jaune McDonald's)
- **Accent**: #ff6b35 (Orange vif)
- **Texte**: #1a1a1a (Noir)

### Typographie
- **Font**: Inter (Google Fonts)
- **Poids**: 400, 500, 600, 700

### Espacements & Rayons
- **Radius**: 12-30px (boutons et cartes)
- **Padding**: 20-50px
- **Gap**: 10-40px

## 💾 Authentification

L'authentification utilise les cookies HTTP secure:
- Les tokens sont stockés en cookies httpOnly (depuis le backend)
- Logout nettoie le localStorage et les cookies
- AuthGuard protège les routes authentifiées

## 📱 Responsive Design

Tous les composants sont fully responsive:
- **Desktop**: Layout complet optimisé
- **Tablet**: Grille adaptée
- **Mobile**: Single column et touches optimisées

## 🛠️ Configuration

Le frontend est pré-configuré pour:
- Requêtes HTTP avec credentials (cookies)
- Routing complet
- Guards d'authentification
- Services centralisés

Aucune configuration supplémentaire n'est nécessaire pour démarrer!
