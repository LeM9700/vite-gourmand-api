from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
import secrets
import logging

from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

def validate_jwt_settings():
    """Valide la configuration JWT au démarrage"""
    try:
        if not hasattr(settings, 'jwt_secret') or not settings.jwt_secret:
            raise RuntimeError("JWT_SECRET n'est pas défini dans les settings")
        
        if len(settings.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET trop court (minimum 32 caractères)")
        
        if not hasattr(settings, 'jwt_alg') or settings.jwt_alg not in ("HS256", "HS384", "HS512"):
            raise RuntimeError(f"Algorithme JWT non sécurisé: {getattr(settings, 'jwt_alg', 'undefined')}")
        
        if not hasattr(settings, 'jwt_expire_minutes') or settings.jwt_expire_minutes <= 0:
            raise RuntimeError("JWT_EXPIRE_MINUTES doit être un nombre positif")
        
        logger.info("✅ Configuration JWT validée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur de validation JWT: {e}")
        raise

# ✅ Validation au démarrage (avec gestion d'erreur)
try:
    validate_jwt_settings()
except Exception as e:
    logger.warning(f"Validation JWT échouée au démarrage: {e}")
    # En développement, on peut continuer, en production on doit arrêter

def create_access_token(subject: str, role: str) -> str:
    """Crée un JWT sécurisé"""
    if not subject or not role:
        raise ValueError("Subject et role obligatoires")
    
    try:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {
            "sub": str(subject),
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16),
            "iss": "vite-gourmand-api"
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    except Exception as e:
        logger.error(f"Erreur création JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération du token"
        )

def verify_jwt_token(token: str):
    """Vérifie et décode un JWT"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        return payload
    except JWTError as e:
        logger.warning(f"JWT invalide: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _ensure_password_not_insane(pwd: str) -> None:
    """Validation de base du mot de passe"""
    if len(pwd.encode("utf-8")) > 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long"
        )

def hash_password(password: str) -> str:
    """Hash sécurisé avec bcrypt"""
    _ensure_password_not_insane(password)
    
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long for bcrypt (max 72 bytes)"
        )
    
    try:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Erreur hash password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du hashage du mot de passe"
        )

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Vérification sécurisée du mot de passe"""
    _ensure_password_not_insane(plain_password)
    
    if len(plain_password.encode("utf-8")) > 72:
        return False

    try:
        pwd_bytes = plain_password.encode('utf-8')
        hashed_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except (ValueError, TypeError, UnicodeError) as e:
        logger.warning(f"Erreur vérification password: {e}")
        return False


