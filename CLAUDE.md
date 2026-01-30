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

- **`src/main.py`** - Application entry point, router registration, CORS configuration, background task lifespan management
- **`src/core/`** - Core utilities
  - `config.py` - Environment configuration (Pydantic Settings)
  - `security.py` - JWT authentication, password hashing
  - `payment.py` - HelloAsso payment client (OAuth2, checkout creation)
  - `exceptions.py` - Custom exception handlers
  - `logging.py` - Structured logging configuration
- **`src/db/`** - Database setup
  - `session.py` - SQLAlchemy session management
  - `base.py` - Base model class
  - `init_db.py` - Database initialization
  - `menu_data.json` - Menu items and categories data (JSON-based, no longer in database)
  - `fix_schema.py` - Schema migration utilities for converting FK columns to VARCHAR
- **`src/auth/`** - Authentication (email verification codes, JWT tokens, email blacklist checking)
- **`src/users/`** - User management (models, schemas, CRUD)
- **`src/reservations/`** - Reservation system
  - `models.py` - MenuItemLimit model for availability tracking
  - `availability.py` - Time slot availability management (7:00-20:00, hourly slots)
- **`src/menu/`** - Menu endpoints
  - `router.py` - Menu API endpoints (loads from JSON)
  - `utils.py` - Menu data loading utilities (`load_menu_data()`)
- **`src/admin/`** - Admin panel endpoints (order management, ghost order view)
- **`src/payments/`** - Payment processing
  - `router.py` - Payment endpoints with idempotent completion logic
  - `helloasso_service.py` - HelloAsso OAuth2 client with token caching
  - `background_tasks.py` - Background payment polling task (runs every 60s)
- **`src/terminal/`** - Terminal/kiosk functionality
- **`src/print/`** - PDF generation (FPDF2, markdown2 rendering)
- **`src/mail.py`** - Email sending (FastAPI-Mail with dual SMTP config)
- **`migration/versions/`** - Alembic database migrations

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
- **`src/pages/`** - Special pages
  - `print.tsx` - Print/batch view for order management
  - `terminal.tsx` - Terminal/kiosk interface

**View States:** `landing | order | order-status | payment-success | payment-error | recap | admin | admin-print | admin-terminal`

The frontend uses view state to manage routing without a router library. URL changes are handled via `window.history.pushState()` and `useEffect` hooks.

### Menu System Architecture

The menu system uses JSON-based configuration instead of database models:

- **Data Source:** `backend/src/db/menu_data.json`
- **Categories:** `cat_boulanger`, `cat_gourmand`, `cat_veget`, `cat_boissons`, `cat_extra`
- **Item IDs:** String format (e.g., `menu_boulanger`, `drink_coca`)
- **Prices:** Stored as numeric values (e.g., `1.00`)
- **Loading:** `load_menu_data()` utility in `src/menu/utils.py`
- **Caching:** Admin panel uses `get_menu_data_cached()` for performance

User menu selections are stored as string IDs (`menu_id`, `boisson_id`) and JSON array (`bonus_ids`) in the User model, not as foreign keys. Multiple extras can be selected.

### Authentication Flow

1. User enters email on landing page
2. Backend validates email against allowed domains (ALLOWED_DOMAINS in auth/service.py)
3. Backend checks email against blacklist (`blacklist.json`)
4. Backend generates 6-character alphanumeric verification code (15min expiration)
5. Email sent via FastAPI-Mail (Mailhog in dev, IONOS SMTP in prod)
6. User verifies code -> receives JWT token (7 days expiration)
7. Optional: BDE membership check via external API
8. JWT token used for authenticated endpoints

**Email Identity:** The system uses canonical email identity (prenom.nom format) separate from delivery email.

### Payment Flow

1. User completes order and provides details
2. Backend creates HelloAsso checkout intent (OAuth2 client credentials with token caching)
3. User redirected to HelloAsso payment page
4. Multiple payment completion paths (all using idempotent `complete_payment()` function):
   - HelloAsso webhook notification
   - User return callback (status polling)
   - Background task polling (every 60s) - catches missed webhooks, closed browsers
5. Backend updates reservation status and sends confirmation email
6. User redirected to success/error page with `status_token` for tracking

### Time Slot Availability System

- **Slots:** Hourly from 7:00-8:00 to 19:00-20:00 (13 slots total)
- **Tracking:** `MenuItemLimit` model with `max_quantity` and `current_quantity`
- **Functions:** `get_available_slots()`, `is_slot_available()` in `reservations/availability.py`

### Database Schema Notes

- **Users table** - Reservation details, payment status, BDE membership, menu selections (string IDs), contact info, `adresse_if_maisel` (Enum for building address)
- **MenuItemLimit table** - Item availability tracking with string `item_id` (matches JSON structure)
- **Migrations** managed via Alembic in `backend/migration/versions/`
- **No menu database tables** - Menu data loaded from JSON file

### External APIs

- **HelloAsso** - Payment processing (OAuth2 with 5-minute token cache, checkout intents, webhooks, status polling)
- **BDE API** - Student membership verification (custom API with API key)
- **SMTP (IONOS)** - Production email sending (via MAIL_HYPNOS_* variables)

### Configuration

All configuration via environment variables (`.env` file):
- Database connection (`DATABASE_URL`)
- JWT secrets (`JWT_SECRET_KEY`)
- Email servers:
  - Development: Mailhog
  - Production: IONOS SMTP (`MAIL_HYPNOS_*` variables - 5 required)
- HelloAsso credentials (`HELLOASSO_CLIENT_ID`, `HELLOASSO_CLIENT_SECRET`)
- HelloAsso redirect URL (`HELLOASSO_REDIRECT_BASE_URL` - separate from FRONTEND_URL)
- BDE API credentials (`BDE_API_URL`, `BDE_API_KEY`)
- Frontend URL for CORS and redirects (`FRONTEND_URL`)

### Docker Services

- **proxy** - Nginx reverse proxy (routes `/api/*` to backend, others to frontend)
- **backend** - FastAPI with uvicorn, hot-reload via `docker compose watch`
- **frontend** - Vite dev server with hot-reload
- **db** - PostgreSQL 18
- **mail** - Mailhog (development email testing, web UI on port 8025)

### Tech Stack

**Backend:**
- Python >= 3.12
- FastAPI 0.115.0+
- SQLAlchemy (async)
- Alembic (migrations)
- FPDF2 (PDF generation)
- markdown2 (markdown rendering)
- python-multipart (form data)

**Frontend:**
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.2.4
- Custom history-based routing (no external router library)

## Important Development Notes

- The API docs are disabled in production (`/docs`, `/redoc` return 404)
- CORS is configured for specific origins including localhost development ports
- JWT tokens expire after 7 days, email verification codes after 15 minutes
- The `docker compose watch` command provides hot-reload for both frontend and backend source changes
- Database migrations should be created via Alembic, not manual SQL (except for `update_db.sh` utility script)
- Payment amounts are in centimes (cents) in HelloAsso API (multiply by 100)
- Admin users have `user_type = 'admin'` in the users table
- Menu data is JSON-based - edit `backend/src/db/menu_data.json` to modify menus
- Background payment task provides resilience for missed webhooks and browser closures
- Email blacklist (`blacklist.json`) prevents specific users from ordering
