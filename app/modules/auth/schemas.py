from pydantic import BaseModel, EmailStr, Field,field_validator
import re
from typing import Optional

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EmailConfirmationIn(BaseModel):
    token: str = Field(min_length=10, description="Token de confirmation reçu par email")


class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    phone: str = Field(min_length=10, max_length=20)
    address: str = Field(min_length=5, max_length=500)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', v):
            raise ValueError('Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes')
        return v.title()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Accepter formats français
        phone_cleaned = re.sub(r'[\s\-\.\(\)]', '', v)
        if not re.match(r'^(\+33|0)[1-9](\d{8})$', phone_cleaned):
            raise ValueError('Numéro de téléphone français invalide')
        return phone_cleaned

class EmployeeCreateIn(BaseModel):
    """Schéma pour la création d'un employé - le rôle est toujours EMPLOYEE (ignoré si fourni)"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    phone: str = Field(min_length=10, max_length=20)
    address: str = Field(min_length=5, max_length=500)
    role: Optional[str] = "EMPLOYEE"  # Ignoré par le backend, toujours forcé à EMPLOYEE
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', v):
            raise ValueError('Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes')
        return v.title()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Accepter formats français
        phone_cleaned = re.sub(r'[\s\-\.\(\)]', '', v)
        if not re.match(r'^(\+33|0)[1-9](\d{8})$', phone_cleaned):
            raise ValueError('Numéro de téléphone français invalide')
        return phone_cleaned

class UserOut(BaseModel):
    id: int
    email: str
    firstname: str
    lastname: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    email_confirmed: Optional[bool] = False
    
    class Config:
        from_attributes = True


class UserUpdateIn(BaseModel):
    """Schéma pour la mise à jour des informations utilisateur"""
    firstname: Optional[str] = Field(None, min_length=2, max_length=50)
    lastname: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', v):
            raise ValueError('Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes')
        return v.title()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        # Accepter formats français
        phone_cleaned = re.sub(r'[\s\-\.\(\)]', '', v)
        if not re.match(r'^(\+33|0)[1-9](\d{8})$', phone_cleaned):
            raise ValueError('Numéro de téléphone français invalide')
        return phone_cleaned
    
    


class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=20, description="Token de réinitialisation reçu par email")
    new_password: str = Field(min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule')
        if not re.search(r'\d', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v
  