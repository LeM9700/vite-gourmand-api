
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
import logging

from app.core.db_postgres import get_db
from app.modules.auth.schemas import LoginIn, TokenOut, UserOut, EmployeeCreateIn, UserRegisterIn, UserUpdateIn, ForgotPasswordIn, ResetPasswordIn
from app.modules.auth.security import verify_password, create_access_token, hash_password
from app.modules.users.models import User
from app.modules.auth.deps import get_current_user, require_admin
from app.core.rate_limiter import rate_limit_login
from app.core.security_logger import log_auth_attempt
from app.core.email_service import email_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenOut)
def login(request: Request,
            form_data: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(get_db),
          _rate_check = Depends(rate_limit_login)
          ):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()
    
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    if user is None or not user.is_active:
        # ✅ Log de la tentative échouée
        log_auth_attempt(form_data.username, False, client_ip, user_agent)
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # IMPORTANT: pour que ça marche avec ton seed actuel,
    # il faut que password_hash soit un vrai bcrypt.
    if not verify_password(form_data.password, user.password_hash):
        # ✅ Log de la tentative échouée
        log_auth_attempt(form_data.username, False, client_ip, user_agent)
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # ✅ Log de la tentative réussie
    log_auth_attempt(form_data.username, True, client_ip, user_agent)
    
    token = create_access_token(subject=str(user.id), role=user.role)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegisterIn, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    stmt = select(User).where(User.email == user_data.email)
    existing_user = db.execute(stmt).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Créer le nouvel utilisateur
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        phone=user_data.phone,          # ✅ Ajouté
        address=user_data.address,
        role="USER",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/create-employee", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreateIn, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    # Vérifier si l'email existe déjà
    stmt = select(User).where(User.email == employee_data.email)
    existing_user = db.execute(stmt).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Sécurité: Forcer le rôle à EMPLOYEE (seuls les admins peuvent créer des employés, pas d'autres admins)
    forced_role = "EMPLOYEE"
    
    # Créer le nouvel employé
    hashed_password = hash_password(employee_data.password)
    new_employee = User(
        email=employee_data.email,
        password_hash=hashed_password,
        firstname=employee_data.firstname,
        lastname=employee_data.lastname,
        phone=employee_data.phone,
        address=employee_data.address,
        role=forced_role,  # ✅ Forcé à EMPLOYEE pour la sécurité
        is_active=True
    )
    
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    # 📧 Envoyer l'email de bienvenue (sans mot de passe)
    try:
        email_sent = email_service.send_employee_welcome_email(
            email=new_employee.email,
            firstname=new_employee.firstname,
            lastname=new_employee.lastname
        )
        if email_sent:
            logger.info(f"✅ Email de bienvenue envoyé à {new_employee.email}")
        else:
            logger.warning(f"⚠️ Échec envoi email de bienvenue à {new_employee.email}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email de bienvenue: {e}")
        # On ne bloque pas la création du compte si l'email échoue
    
    return new_employee

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(
    user_data: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour les informations de l'utilisateur connecté"""
    
    # Mettre à jour uniquement les champs fournis
    if user_data.firstname is not None:
        current_user.firstname = user_data.firstname
    if user_data.lastname is not None:
        current_user.lastname = user_data.lastname
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.address is not None:
        current_user.address = user_data.address
    
    db.commit()
    db.refresh(current_user)
    
    return current_user




@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    payload: ForgotPasswordIn,
    db: Session = Depends(get_db)
):
    """Demande de réinitialisation de mot de passe"""
    from app.modules.auth.security import create_access_token
    from app.core.config import settings
    
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalar_one_or_none()
    
    # ⚠️ Toujours renvoyer 200 pour ne pas divulguer si l'email existe
    if not user or not user.is_active:
        logger.warning(f"⚠️ Tentative reset password pour email inexistant: {payload.email}")
        return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}
    
    # Créer un token JWT spécial pour le reset (expire 1h)
    reset_token = create_access_token(
        subject=f"reset:{user.id}",
        role="RESET",
    )
    
    # Envoyer l'email avec deep link (pas besoin de frontend_url)
    try:
        email_sent = email_service.send_password_reset_email(
            user_email=user.email,
            user_name=user.full_name,
            reset_token=reset_token,
        )
        if email_sent:
            logger.info(f"✅ Email reset password envoyé à {user.email}")
        else:
            logger.warning(f"⚠️ Échec envoi email reset à {user.email}")
    except Exception as e:
        logger.error(f"❌ Erreur envoi email reset: {e}")
    
    return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordIn,
    db: Session = Depends(get_db)
):
    """Réinitialise le mot de passe avec le token reçu par email"""
    from jose import jwt, JWTError
    from app.core.config import settings
    from app.modules.auth.security import hash_password
    
    # Décoder le token
    try:
        decoded = jwt.decode(payload.token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        subject = decoded.get("sub")
        
        if not subject or not subject.startswith("reset:"):
            raise ValueError("Token invalide")
        
        user_id = int(subject.split(":")[1])
    except (JWTError, ValueError, IndexError) as e:
        logger.warning(f"⚠️ Token reset invalide: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
    
    # Récupérer l'utilisateur
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    # Changer le mot de passe
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    
    logger.info(f"✅ Mot de passe réinitialisé pour user_id={user_id}")
    return {"message": "Mot de passe réinitialisé avec succès"}




@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Endpoint de déconnexion (côté client supprime le token)"""
    return {"message": "Déconnexion réussie"}