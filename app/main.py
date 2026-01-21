from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import SecurityMiddleware
from app.core.exceptions import global_exception_handler
from app.modules.menus.router import router as menus_router
from app.modules.auth.router import router as auth_router
from app.modules.orders.router import router as orders_router
from app.modules.admin_stats.router import router as admin_stats
from app.modules.contact.router import router as contact_router
from app.modules.menus.router_dishes import router as dishes_router
from app.modules.reviews.router import router as reviews_router
from app.modules.schedules.router import router as schedules_router
from app.modules.admin_employees.router import router as admin_employees_router 



# ✅ AJOUTEZ TOUS LES IMPORTS DE MODÈLES POUR QUE SQLAlchemy LES CONNAISSE
from app.modules.users.models import User  # ✅ Ajoutez cette ligne

# ✅ AJOUTEZ CES IMPORTS
from app.core.db_base import Base
from app.core.db_postgres import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    #Validation de la configuration
    from app.modules.auth.security import validate_jwt_settings
    validate_jwt_settings()
    
    # Création des tables au démarrage
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown (si nécessaire)

# ✅ UTILISEZ LE LIFESPAN AU LIEU DE on_event
app_kwargs = { "title":settings.api_title,
        "version":settings.api_version,
        "lifespan":lifespan
}

if settings.environment == "production":
    app_kwargs.update(docs_url=None, redoc_url=None, openapi_url=None)

app=FastAPI(**app_kwargs)

#Middleware de sécurité en 1 
app.add_middleware(SecurityMiddleware)  

#CORS sécurisé
if settings.environment == "production":
    cors_origins = [
        "https://vitegourmand.netlify.app",
        "https://www.vitegourmand.netlify.app",
        settings.frontend_url.rstrip('/') if settings.frontend_url else "",
    ]
    # Filtrer les valeurs vides
    cors_origins = [origin for origin in cors_origins if origin]
    logger.info(f"✅ CORS configured for production: {cors_origins}")
else : 
    cors_origins = ["*"]
    logger.info("🚨 CORS enabled for development (allow all)")

# Middleware custom pour logger les requêtes CORS
@app.middleware("http")
async def log_cors_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin:
        logger.info(f"🌐 Request from origin: {origin}")
        if origin not in cors_origins and "*" not in cors_origins:
            logger.warning(f"⚠️ CORS rejected origin: {origin} - Allowed: {cors_origins}")
    
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)        

# Handler d'exeptions global
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
def root():
    return {"message": "Vite & Gourmand API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment, "version": settings.api_version, "timestamp": datetime.now().isoformat()}

app.include_router(menus_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(admin_stats)
app.include_router(contact_router)
app.include_router(dishes_router)
app.include_router(reviews_router)
app.include_router(schedules_router)
app.include_router(admin_employees_router)

