from sqlalchemy.orm import Session
from typing import List
from datetime import time
from . import models, schemas

class ScheduleService:
    @staticmethod
    def _parse_time(time_str: str | None) -> time | None:
        """Convertir une chaîne HH:MM en objet time"""
        if not time_str:
            return None
        try:
            hours, minutes = map(int, time_str.split(':'))
            return time(hours, minutes)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _format_time(time_obj: time | None) -> str | None:
        """Convertir un objet time en chaîne HH:MM"""
        if not time_obj:
            return None
        return time_obj.strftime('%H:%M')

    @staticmethod
    def get_all_schedules(db: Session) -> List[dict]:
        """Récupérer tous les horaires"""
        schedules = db.query(models.Schedule).order_by(models.Schedule.day_of_week).all()
        return [
            {
                'id': s.id,
                'day_of_week': s.day_of_week,
                'open_time': ScheduleService._format_time(s.open_time),
                'close_time': ScheduleService._format_time(s.close_time),
                'is_closed': s.is_closed
            }
            for s in schedules
        ]

    @staticmethod
    def get_schedule_by_id(db: Session, schedule_id: int) -> dict | None:
        """Récupérer un horaire par ID"""
        schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not schedule:
            return None
        return {
            'id': schedule.id,
            'day_of_week': schedule.day_of_week,
            'open_time': ScheduleService._format_time(schedule.open_time),
            'close_time': ScheduleService._format_time(schedule.close_time),
            'is_closed': schedule.is_closed
        }

    @staticmethod
    def create_schedule(db: Session, schedule_data: schemas.ScheduleCreate) -> dict:
        """Créer un nouvel horaire"""
        db_schedule = models.Schedule(
            day_of_week=schedule_data.day_of_week,
            open_time=ScheduleService._parse_time(schedule_data.open_time),
            close_time=ScheduleService._parse_time(schedule_data.close_time),
            is_closed=schedule_data.is_closed
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return {
            'id': db_schedule.id,
            'day_of_week': db_schedule.day_of_week,
            'open_time': ScheduleService._format_time(db_schedule.open_time),
            'close_time': ScheduleService._format_time(db_schedule.close_time),
            'is_closed': db_schedule.is_closed
        }

    @staticmethod
    def update_schedule(db: Session, schedule_id: int, schedule_data: schemas.ScheduleUpdate) -> dict | None:
        """Mettre à jour un horaire"""
        db_schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not db_schedule:
            return None
        
        db_schedule.day_of_week = schedule_data.day_of_week
        db_schedule.open_time = ScheduleService._parse_time(schedule_data.open_time)
        db_schedule.close_time = ScheduleService._parse_time(schedule_data.close_time)
        db_schedule.is_closed = schedule_data.is_closed
        
        db.commit()
        db.refresh(db_schedule)
        return {
            'id': db_schedule.id,
            'day_of_week': db_schedule.day_of_week,
            'open_time': ScheduleService._format_time(db_schedule.open_time),
            'close_time': ScheduleService._format_time(db_schedule.close_time),
            'is_closed': db_schedule.is_closed
        }

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> bool:
        """Supprimer un horaire"""
        db_schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
        if not db_schedule:
            return False
        
        db.delete(db_schedule)
        db.commit()
        return True
