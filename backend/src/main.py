from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.reservations.router import router as reservations_router
from src.admin.router import router as admin_router
from src.menu.router import router as menu_router
from src.print.router import router as print_router
from src.payments.router import router as payments_router
from src.terminal.router import router as terminal_router
from src.payments.background_tasks import start_background_tasks
from src.core.config import settings
from src.db.base import Base
from src.db.session import engine
from src.db.init_db import init_db
# Importer les modèles pour que SQLAlchemy les enregistre
from src.users.models import User

# Créer les tables (à remplacer par Alembic en prod)
Base.metadata.create_all(bind=engine)

init_db()  # Lance au démarrage de l'app

# Désactiver la documentation en production
is_production = settings.ENVIRONMENT == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Starts background tasks on startup and cancels them on shutdown.
    """
    # Startup: Start background tasks
    print("[STARTUP] Starting background tasks...")
    background_task = await start_background_tasks()

    yield

    # Shutdown: Cancel background tasks
    print("[SHUTDOWN] Cancelling background tasks...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        print("[SHUTDOWN] Background tasks cancelled")


app = FastAPI(
    title="MC INT API",
    description="API pour réservations MC INT avec auth email/code, BDE check et paiement HelloAsso",
    version="1.0.0",
    root_path="/api",
    lifespan=lifespan,
    # Désactiver /docs, /redoc et /openapi.json en production
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# CORS - build allowed origins list
allowed_origins = [
    "https://dej.hypnos2026.fr",
    "http://localhost:4200",
    "http://localhost:5173",
]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(reservations_router, prefix="/reservations", tags=["reservations"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(menu_router, prefix="/menu", tags=["menu"])
app.include_router(print_router, prefix="/print", tags=["print"])
app.include_router(payments_router, tags=["payments"])
app.include_router(terminal_router, prefix="/terminal", tags=["terminal"])



@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "MC INT API running"}

