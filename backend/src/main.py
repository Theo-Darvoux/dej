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
from src.core.config import settings
from src.db.base import Base
from src.db.session import engine
from src.db.init_db import init_db
from src.db.init_menu import init_menu_data

# Importer les modèles pour que SQLAlchemy les enregistre
from src.users.models import User
from src.menu.models import Category, MenuItem

# Créer les tables (à remplacer par Alembic en prod)
Base.metadata.create_all(bind=engine)

init_db()  # Lance au démarrage de l'app
init_menu_data()

# Désactiver la documentation en production
is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="MC INT API",
    description="API pour réservations MC INT avec auth email/code, BDE check et paiement HelloAsso",
    version="1.0.0",
    root_path="/api",
    # Désactiver /docs, /redoc et /openapi.json en production
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:4200"],
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

