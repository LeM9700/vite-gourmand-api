from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

ALLOWED_MESSAGE_STATUSES = {"SENT", "FAILED", "ARCHIVED", "TREATED"}

class ContactCreateIn(BaseModel):
    email: EmailStr
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=4000)

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
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ALLOWED_MESSAGE_STATUSES:
            raise ValueError(
                f"Statut invalide '{v}'. Valeurs autorisées : {', '.join(sorted(ALLOWED_MESSAGE_STATUSES))}"
            )
        return v
