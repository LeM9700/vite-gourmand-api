from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.modules.contact.models import ContactMessage
from app.modules.contact.schemas import ALLOWED_MESSAGE_STATUSES

def create_contact_message(db: Session, email: str, title: str, description: str) -> ContactMessage:
    msg = ContactMessage(
        email=email,
        title=title,
        description=description,
        status="SENT",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def list_contact_messages(db: Session) -> list[ContactMessage]:
    stmt = select(ContactMessage).order_by(desc(ContactMessage.created_at))
    return db.execute(stmt).scalars().all()

def patch_contact_status(db: Session, message_id: int, status: str) -> ContactMessage:
    if status not in ALLOWED_MESSAGE_STATUSES:
        raise HTTPException(status_code=400, detail="Statut invalide (SENT/FAILED/ARCHIVED/TREATED)")

    msg = db.execute(select(ContactMessage).where(ContactMessage.id == message_id)).scalar_one_or_none()
    if msg is None:
        raise HTTPException(status_code=404, detail="Message introuvable")

    msg.status = status
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
