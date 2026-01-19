from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ReviewCreateIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=5)

class CustomerInfoOut(BaseModel):
    """Infos client pour les reviews"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    firstname: str
    lastname: str

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    user_id: int
    rating: int
    comment: str
    status: str
    created_at: datetime
    moderated_by_user_id: int | None = None
    moderated_at: datetime | None = None
    customer: CustomerInfoOut | None = None

class ReviewModerateIn(BaseModel):
    status: str = Field(min_length=7, max_length=8)  # APPROVED/REJECTED


class ReviewPublicOut(BaseModel):
    """Schema pour l'affichage public des avis (avec nom du client)"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    rating: int
    comment: str
    created_at: datetime
    customer_name: str | None = None