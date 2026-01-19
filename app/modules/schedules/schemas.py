from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

class ScheduleBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Lundi, 6=Dimanche")
    open_time: Optional[str] = Field(None, description="Heure d'ouverture (HH:MM)")
    close_time: Optional[str] = Field(None, description="Heure de fermeture (HH:MM)")
    is_closed: bool = Field(default=False, description="Jour fermé")

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(ScheduleBase):
    pass

class ScheduleResponse(BaseModel):
    id: int
    day_of_week: int
    open_time: Optional[str]
    close_time: Optional[str]
    is_closed: bool

    class Config:
        from_attributes = True
