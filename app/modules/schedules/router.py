from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db_postgres import get_db
from app.modules.auth.deps import require_employee_or_admin
from app.modules.users.models import User
from . import schemas
from .service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["Schedules"])

@router.get("", response_model=List[schemas.ScheduleResponse])
def get_all_schedules(
    db: Session = Depends(get_db)
):
    """Récupérer tous les horaires (public)"""
    schedules = ScheduleService.get_all_schedules(db)
    return schedules

@router.post("", response_model=schemas.ScheduleResponse)
def create_schedule(
    schedule_data: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee_or_admin)
):
    """Créer un horaire (EMPLOYEE/ADMIN uniquement)"""
    schedule = ScheduleService.create_schedule(db, schedule_data)
    return schedule

@router.put("/{schedule_id}", response_model=schemas.ScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule_data: schemas.ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee_or_admin)
):
    """Mettre à jour un horaire (EMPLOYEE/ADMIN uniquement)"""
    schedule = ScheduleService.update_schedule(db, schedule_id, schedule_data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Horaire introuvable")
    return schedule

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee_or_admin)
):
    """Supprimer un horaire (EMPLOYEE/ADMIN uniquement)"""
    success = ScheduleService.delete_schedule(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Horaire introuvable")
    return {"message": "Horaire supprimé avec succès"}
