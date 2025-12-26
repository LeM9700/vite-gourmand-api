from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.db_postgres import get_db
from app.modules.auth.schemas import LoginIn, TokenOut
from app.modules.auth.security import verify_password, create_access_token
from app.modules.users.models import User
from app.modules.auth.deps import get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # IMPORTANT: pour que ça marche avec ton seed actuel,
    # il faut que password_hash soit un vrai bcrypt.
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token = create_access_token(subject=str(user.id), role=user.role)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
