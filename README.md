# 🍔 MC INT - Plateforme de Réservation Moderne

## 📋 Vue d'ensemble

MC INT est une plateforme web moderne de réservation avec un design inspiré par McDonald's et développée avec les principes visuels de Monks. Une application full-stack composée d'un backend FastAPI robuste et d'un frontend Angular élégant.

## 🎨 Design & Styling

### Concept visuel
- **Inspiration principale**: McDonald's (couleurs vives, design épuré)
- **Style des interactions**: Monks (animations fluides, gradients modernes, effects organiques)
- **Palette couleurs**:
  - 🔴 Rouge primaire: `#dc143c` - L'emblème McDonald's
  - 🟡 Jaune secondaire: `#ffc72c` - Accent McDonald's  
  - 🟠 Orange accent: `#ff6b35` - Dynamisme et énergie
  - ⚫ Noir texte: `#1a1a1a` - Lisibilité optimale

### Effets visuels Monks
1. **Blob Animations** - Formes organiques flottantes en arrière-plan
2. **Gradients fluides** - Rouge → Rose → Violet
3. **Animations d'entrée** - Fade Up, Slide In Right
4. **Hover Effects** - Élévation, ombre, changement de couleur
5. **Micro-interactions** - Spinners, transitions lisses

## 🏗️ Architecture Backend

### Stack technologique
- **Framework**: FastAPI
- **ORM**: SQLAlchemy  
- **Base de données**: PostgreSQL
- **Auth**: JWT + Cookies HttpOnly
- **Email**: Async SMTP
- **Paiement**: HelloAsso API

### Endpoints principaux
```
POST /api/auth/request-code        # Envoyer code par email
POST /api/auth/verify              # Vérifier code + check BDE
POST /api/reservations/            # Créer réservation
GET  /api/reservations/my          # Mes réservations
DELETE /api/reservations/{id}      # Annuler réservation
GET  /api/admin/reservations       # Admin: voir tout
```

### Flux d'authentification
1. User rentre email → Code 6 chiffres généré + email envoyé
2. User rentre code → Vérification BDE API  
3. JWT émis + stocké en cookie HttpOnly secure
4. Session protégée via AuthGuard

## 🎯 Frontend Angular

### Structure des pages

#### 1. **Login** (`/login`)
- Formulaire simple email
- Design minimaliste avec blobs animés
- Feedback utilisateur (loading, erreur, succès)

#### 2. **Verify** (`/verify`)
- 6 inputs numériques auto-focus
- Bouton "Renvoyer le code"
- Transitions fluides

#### 3. **Reservation** (`/reservation`)
- Date & heure de livraison
- Choix: résidence ou adresse externe
- Formulaire conditionnel

#### 4. **Dashboard** (`/dashboard`)
- Liste de réservations en grid responsive
- Statut par couleur (pending, confirmed, paid, cancelled)
- Actions: Payer, Annuler

### Services
```typescript
AuthService        # Gestion auth + tokens
ReservationService # CRUD réservations
AuthGuard          # Protection routes
```

## 📱 Responsive Design

- **Desktop** (>1024px): Layout complet optimisé
- **Tablet** (768-1024px): Grille adaptée 2 colonnes
- **Mobile** (<768px): Single column, touches tactiles
- **Touches tactiles**: Input numériques optimisés

## 🚀 Déploiement

### Frontend
```bash
# Installation
cd frontend && npm install

# Développement
npm start

# Build production
npm run build
# Output: dist/frontend/
```

### Backend
```bash
# Installation
cd backend && pip install -r requirements.txt

# Développement
uvicorn src.main:app --reload

# Production avec Docker
docker build -f DockerFile.prod -t mc-int-backend .
```

### Docker Compose (Complet)
```bash
# Production
docker-compose -f docker-compose.prod.yml up -d

# Développement
docker-compose up -d
```

## 🔐 Sécurité

- ✅ CORS configuré (`frontend_url` + localhost)
- ✅ Cookies HttpOnly + Secure
- ✅ JWT + Refresh tokens
- ✅ Validation email + code
- ✅ Rate limiting (à implémenter)
- ✅ HTTPS en production

## 📊 Base de données

### Modèles principaux
```
User
├── id (UUID)
├── email (unique)
├── code_verification
├── code_expires_at
├── is_verified
├── is_cotisant_bde
└── created_at

Reservation
├── id (UUID)
├── user_id (FK)
├── date_reservation
├── heure_reservation
├── habite_residence
├── numero_chambre
├── numero_immeuble
├── adresse
├── status (pending, confirmed, paid, cancelled)
├── payment_link (HelloAsso)
└── created_at
```

## 🔄 Flux complet

```
1. User accède /login
   ↓
2. Entre email → Backend envoie code
   ↓
3. Redirect /verify?email=...
   ↓
4. Entre code → Vérification + BDE check
   ↓
5. Authentifié (JWT cookie)
   ↓
6. Si cotisant → /reservation
   Sinon → /dashboard
   ↓
7. Crée réservation → Lien paiement HelloAsso
   ↓
8. Paie → Confirmation instantanée
```

## 🎨 Variables & Constantes

### SCSS Global
```scss
$primary-color: #dc143c;     // Rouge
$secondary-color: #ffc72c;   // Jaune
$accent-color: #ff6b35;      // Orange
$dark-color: #1a1a1a;        // Noir
$light-bg: #fff5f7;          // Beige clair
```

### Animations
- `fadeInUp` - Apparition bas vers haut (0.8s)
- `slideInRight` - Glissement depuis gauche (0.8s)
- `slideDown` - Glissement vers bas (0.6s)
- `blobAnimation` - Mouvement organique (8s infini)
- `spin` - Rotation chargement (0.8s)

## 📦 Dépendances clés

**Backend**
- fastapi==0.104.1
- sqlalchemy==2.0.23
- python-jose[cryptography]==3.3.0
- aiosmtplib==2.1.1
- httpx==0.25.0

**Frontend**
- @angular/core==20.3.0
- @angular/common==20.3.0
- @angular/forms==20.3.0
- sass==1.69.5

## 🛠️ Configuration nécessaire

### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@localhost/mcint
FRONTEND_URL=http://localhost:4200
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
BDE_API_URL=https://api.bde.com
BDE_API_KEY=your-key
HELLOASSO_API_URL=https://api.helloasso.com
HELLOASSO_API_KEY=your-key
```

### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

## 📝 Scripts utiles

```bash
# Frontend
npm run build              # Build production
npm start                  # Démarrage dev
npm test                   # Tests
npm run lint               # Lint

# Backend
python -m pytest           # Tests
black src/                 # Formater code
flake8 src/                # Lint
```

## 🎓 Notes de développement

### Ajouts recommandés futurs
- 📧 Email de confirmation de paiement
- 🔔 Notifications push
- 📱 App mobile native
- 💾 Sauvegarde brouillons
- 🌙 Mode sombre
- 🌍 Multilingue (FR/EN)
- 📊 Dashboard admin avancé
- 📈 Analytics & rapports

### Points d'amélioration
- Rate limiting on endpoints
- Refresh token rotation
- Two-factor authentication (2FA)
- Webhook HelloAsso pour paiements
- Caching Redis
- CDN pour assets

## 📞 Support

Pour toute question sur:
- **Frontend**: Consultez le [DESIGN.md](./frontend/DESIGN.md)
- **Backend**: Consultez le [README](./backend/README.md)
- **Docker**: Consultez [docker-compose.yml](./docker-compose.yml)

---

**Version**: 1.0.0  
**Dernière mise à jour**: Décembre 2025  
**Statut**: Production Ready ✅
