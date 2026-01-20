from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
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
        "https://vite-et-gourmand.fr",
        "https://www.vite-et-gourmand.fr",
    ]
    allowed_credentials = True
    print("✅ CORS configured for production")
else : 
    cors_origins = ["*"]
    allowed_credentials = False
    print("🚨 CORS enabled for development")
    
  

    
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if settings.environment == "production" else cors_origins, 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE","OPTIONS"],
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

