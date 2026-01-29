# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mc'INT is an event reservation system with online ordering, payment integration, and admin management capabilities. The system handles menu reservations with HelloAsso payment processing and BDE (student organization) membership verification.

## Development Commands

### Docker Compose

```bash
# Development with hot-reload
docker compose watch

# Production
docker compose -f docker-compose.prod.yml up

# Stop services
docker compose down
```

### Backend (Python/FastAPI)

Located in `backend/` directory.

```bash
# Run tests (inside backend container)
docker compose exec backend pytest

# Run specific test
docker compose exec backend pytest tests/test_specific.py

# Database migrations (Alembic)
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1

# Access backend shell
docker compose exec backend bash

# Run database update script
./scripts/update_db.sh

# Manage admins
./scripts/add_admin.sh email@example.com
./scripts/add_admin.sh --list
./scripts/add_admin.sh --remove email@example.com
```

### Frontend (React/TypeScript/Vite)

Located in `frontend/` directory.

```bash
# Run linter
cd frontend && npm run lint

# Build for production
cd frontend && npm run build

# Development server (standalone, not recommended - use docker compose watch)
cd frontend && npm run dev

# Preview production build
cd frontend && npm run preview
```

### Database Access

```bash
# Access PostgreSQL directly
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# View logs
docker compose logs db
docker compose logs backend
docker compose logs frontend
```

## Architecture

### Backend Structure

The backend follows a modular router-based architecture with FastAPI:

- **`src/main.py`** - Application entry point, router registration, CORS configuration
- **`src/core/`** - Core utilities
  - `config.py` - Environment configuration (Pydantic Settings)
  - `security.py` - JWT authentication, password hashing
  - `payment.py` - HelloAsso payment client (OAuth2, checkout creation)
  - `exceptions.py` - Custom exception handlers
- **`src/db/`** - Database setup
  - `session.py` - SQLAlchemy session management
  - `base.py` - Base model class
  - `init_db.py` - Database initialization
  - `init_menu.py` - Menu data seeding
- **`src/auth/`** - Authentication (email verification codes, JWT tokens)
- **`src/users/`** - User management (models, schemas, CRUD)
- **`src/reservations/`** - Reservation system
- **`src/menu/`** - Menu items, categories (models with foreign keys)
- **`src/admin/`** - Admin panel endpoints
- **`src/payments/`** - Payment processing (HelloAsso webhooks)
- **`src/terminal/`** - Terminal/kiosk functionality
- **`src/print/`** - PDF generation (FPDF2, markdown rendering)
- **`src/mail.py`** - Email sending (FastAPI-Mail with dual SMTP config)
- **`migration/`** - Alembic database migrations

### Frontend Structure

Single-page React application with client-side routing:

- **`src/App.tsx`** - Main app component with view state routing
- **`src/context/MenuContext.tsx`** - Global menu state management
- **`src/components/`** - Reusable components
  - `landing/` - Landing page
  - `order/` - Multi-step order flow
    - `steps/` - Individual order steps (MenuSelection, EmailVerification, Delivery, Checkout, etc.)
  - `admin/` - Admin dashboard
  - `payment/` - Payment success/error pages
  - `recap/` - Reservation summary
  - `popup/` - Modal components
  - `cart-bar/`, `category-slider/`, `menucard/`, `sidebar/` - UI components
- **`src/pages/`** - Special pages (print, terminal)

The frontend uses view state (`landing | order | order-status | payment-success | payment-error | recap | admin`) to manage routing without a router library. URL changes are handled via `window.history.pushState()` and `useEffect` hooks.

### Authentication Flow

1. User enters email on landing page
2. Backend generates 6-digit verification code (15min expiration)
3. Email sent via FastAPI-Mail (Mailhog in dev, IONOS SMTP in prod)
4. User verifies code → receives JWT token (7 days expiration)
5. Optional: BDE membership check via external API
6. JWT token used for authenticated endpoints

### Payment Flow

1. User completes order and provides details
2. Backend creates HelloAsso checkout intent (OAuth2 client credentials)
3. User redirected to HelloAsso payment page
4. HelloAsso webhook notifies backend of payment status
5. Backend updates reservation status and sends confirmation email
6. User redirected to success/error page

### Database Schema Notes

- **Users table** has extensive fields: reservation details, payment status, BDE membership, menu selections (foreign keys to menu items), contact info
- **Menu system** uses Categories and MenuItems with `external_id` for syncing, limits/thresholds for availability
- **Migrations** managed via Alembic but `Base.metadata.create_all()` is also called in main.py (should rely on Alembic in production)
- **Scripts** (`update_db.sh`) can add missing columns for schema updates

### External APIs

- **HelloAsso** - Payment processing (OAuth2, checkout intents, webhooks)
- **BDE API** - Student membership verification (custom API with API key)
- **SMTP (IONOS)** - Production email sending

### Configuration

All configuration via environment variables (`.env` file):
- Database connection (`DATABASE_URL`)
- JWT secrets (`JWT_SECRET_KEY`)
- Email servers (dual config: Mailhog for dev, IONOS for prod)
- HelloAsso credentials (`HELLOASSO_CLIENT_ID`, `HELLOASSO_CLIENT_SECRET`)
- BDE API credentials (`BDE_API_URL`, `BDE_API_KEY`)
- Frontend URL for CORS and redirects

### Docker Services

- **proxy** - Nginx reverse proxy (routes `/api/*` to backend, others to frontend)
- **backend** - FastAPI with uvicorn, hot-reload via `docker compose watch`
- **frontend** - Vite dev server with hot-reload
- **db** - PostgreSQL 18
- **mail** - Mailhog (development email testing, web UI on port 8025)

## Important Development Notes

- The API docs are disabled in production (`/docs`, `/redoc` return 404)
- CORS is configured for specific origins including localhost development ports
- JWT tokens expire after 7 days, email verification codes after 15 minutes
- The `docker compose watch` command provides hot-reload for both frontend and backend source changes
- Database migrations should be created via Alembic, not manual SQL (except for `update_db.sh` utility script)
- Payment amounts are in centimes (cents) in HelloAsso API (multiply by 100)
- Admin users have `user_type = 'admin'` in the users table
