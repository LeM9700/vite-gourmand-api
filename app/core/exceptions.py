from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ViteGourmandException(Exception):
    """Exception de base pour l'application"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class BusinessLogicError(ViteGourmandException):
    """Erreurs de logique métier"""
    pass

class ValidationError(ViteGourmandException):
    """Erreurs de validation"""
    pass

async def global_exception_handler(request: Request, exc: Exception):
    """Handler global pour les exceptions non gérées"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Ne jamais exposer les détails techniques en prod
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Une erreur inattendue s'est produite",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )