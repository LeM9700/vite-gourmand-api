from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# Configuration moteur selon le type de DB
if settings.postgres_url.startswith("sqlite"):
    engine = create_engine(
        settings.postgres_url, 
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}  # Pour SQLite
    )
else:
    engine = create_engine(settings.postgres_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
