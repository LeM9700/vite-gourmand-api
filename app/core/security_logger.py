import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


# ✅ Créer le dossier logs s'il n'existe pas
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configuration logging sécurisé
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# ✅ Éviter les doublons de handlers
if not security_logger.handlers:
    # ✅ Handler avec rotation (10MB max, 5 fichiers de backup)
    security_handler = RotatingFileHandler(
        "logs/security.log", 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    security_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False

def log_auth_attempt(email: str, success: bool, ip: str, user_agent: str = None):
    """Log des tentatives d'authentification"""
    email_clean = email.replace('\n', '').replace('\r', '').replace('\t', ' ')
    user_agent_clean = (user_agent or "Unknown").replace('\n', '').replace('\r', '').replace('\t', ' ')
    
    status = "SUCCESS" if success else "FAILED"
    security_logger.info(
        f"AUTH_{status} - Email: {email_clean} - IP: {ip} - UserAgent: {user_agent_clean}"
    )

def log_privilege_escalation(user_id: int, action: str, ip: str):
    """Log des actions privilégiées"""
    action_clean = action.replace('\n', '').replace('\r', '').replace('\t', ' ')
    
    security_logger.warning(
        f"PRIVILEGED_ACTION - UserID: {user_id} - Action: {action_clean} - IP: {ip}"
    )

def log_security_event(event_type: str, details: str, ip: str, user_id: int = None):
    """Log général pour événements de sécurité"""
    details_clean = details.replace('\n', '').replace('\r', '').replace('\t', ' ')
    user_info = f"UserID: {user_id}" if user_id else "Anonymous"
    
    security_logger.warning(
        f"SECURITY_EVENT - Type: {event_type} - {user_info} - IP: {ip} - Details: {details_clean}"
    )