from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
import logging

from app.core.db_postgres import get_db
from app.modules.auth.deps import require_admin
from app.modules.users.models import User
from app.modules.admin_employees.schemas import (
    EmployeeListOut,
    EmployeeToggleActiveIn,
    EmployeeToggleActiveOut
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/employees", tags=["Admin Employees"])


@router.get("", response_model=List[EmployeeListOut])
def get_all_employees(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Récupère la liste de tous les employés (EMPLOYEE + ADMIN).
    Accessible uniquement par un administrateur.
    """
    stmt = select(User).where(
        User.role.in_(["EMPLOYEE", "ADMIN"])
    ).order_by(User.created_at.desc())
    
    employees = db.execute(stmt).scalars().all()
    
    logger.info(f"👤 Admin {current_admin.email} a consulté la liste des {len(employees)} employés")
    
    return employees


@router.patch("/{employee_id}/toggle-active", response_model=EmployeeToggleActiveOut)
def toggle_employee_active_status(
    employee_id: int,
    toggle_data: EmployeeToggleActiveIn,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Active ou désactive un compte employé.
    
    ⚠️ IMPORTANT : 
    - Seul un ADMIN peut modifier le statut
    - On ne peut pas désactiver son propre compte (protection)
    - Un compte désactivé ne peut plus se connecter
    
    Cas d'usage : départ d'un employé, suspension temporaire, réactivation
    """
    
    # Vérifier que l'employé existe
    stmt = select(User).where(User.id == employee_id)
    employee = db.execute(stmt).scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé introuvable"
        )
    
    # Vérifier que c'est bien un employé/admin
    if employee.role not in ["EMPLOYEE", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur n'est pas un employé"
        )
    
    # 🚨 Protection : empêcher un admin de se désactiver lui-même
    if employee.id == current_admin.id and not toggle_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
    
    # Mettre à jour le statut
    old_status = employee.is_active
    employee.is_active = toggle_data.is_active
    
    db.commit()
    db.refresh(employee)
    
    # Message de confirmation approprié
    action = "activé" if toggle_data.is_active else "désactivé"
    message = f"Le compte de {employee.firstname} {employee.lastname} a été {action} avec succès."
    
    # Log de l'action pour audit
    logger.info(
        f"🔄 Admin {current_admin.email} a {action} le compte de "
        f"{employee.email} (ID: {employee.id}). Statut: {old_status} → {employee.is_active}"
    )
    
    return {
        "id": employee.id,
        "email": employee.email,
        "firstname": employee.firstname,
        "lastname": employee.lastname,
        "is_active": employee.is_active,
        "message": message
    }
