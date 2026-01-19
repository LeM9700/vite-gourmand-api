from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class EmployeeListOut(BaseModel):
    """Schéma pour la liste des employés (vue admin)"""
    id: int
    email: str
    firstname: str
    lastname: str
    phone: str
    address: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeToggleActiveIn(BaseModel):
    """Schéma pour activer/désactiver un employé"""
    is_active: bool


class EmployeeToggleActiveOut(BaseModel):
    """Réponse après modification du statut"""
    id: int
    email: str
    firstname: str
    lastname: str
    is_active: bool
    message: str
    
    class Config:
        from_attributes = True
