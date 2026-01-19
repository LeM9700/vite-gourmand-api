from sqlalchemy import Column, Integer, String, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db_base import Base
from datetime import time

class Schedule(Base):
    __tablename__ = "opening_hours"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 0=Lundi, 6=Dimanche
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)  # Heure d'ouverture
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)  # Heure de fermeture
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Fermé ce jour
