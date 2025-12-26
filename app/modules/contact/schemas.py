from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

ALLOWED_MESSAGE_STATUSES = {"SENT", "FAILED", "ARCHIVED", "TREATED"}

class ContactCreateIn(BaseModel):
    email: EmailStr
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10)

class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    title: str
    description: str
    status: str
    created_at: datetime

class ContactStatusPatchIn(BaseModel):
    status: str
