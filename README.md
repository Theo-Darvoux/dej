# Mc'INT

Système de réservation pour les events.

---

## 🚀 Lancer le projet

### Développement

```bash
docker compose watch
```

### Production

```bash
docker compose -f docker-compose.prod.yml up
```

---

## 🛠️ Technologies

### Backend
- **Python 3.13**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Alembic** - Migrations de base de données
- **PostgreSQL** - Base de données
- **Uvicorn** - Serveur ASGI
- **Pydantic** - Validation de données
- **FastAPI-Mail** - Envoi d'emails
- **WeasyPrint** - Génération de PDF
- **Passlib + bcrypt** - Hachage de mots de passe
- **python-jose** - JWT pour l'authentification

### Frontend
- **React 19**
- **TypeScript**
- **Vite** - Build tool

### Infrastructure
- **Docker & Docker Compose**
- **Nginx** - Reverse proxy (production)

---

## 🔌 APIs externes

| API | Description |
|-----|-------------|
| **HelloAsso** | Paiement en ligne (checkout) |
| **BDE API** | Vérification des adhérents BDE |
| **SMTP (IONOS)** | Envoi d'emails en production |

---

## ⚙️ Configuration

Copier `.envexample` vers `.env` et renseigner les variables :

```bash
cp .envexample .env
```
