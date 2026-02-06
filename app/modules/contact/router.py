from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db_postgres import get_db
from app.core.rate_limiter import rate_limit_contact
from app.modules.auth.deps import require_employee_or_admin
from app.modules.contact.schemas import ContactCreateIn, ContactOut, ContactStatusPatchIn
from app.modules.contact.service import create_contact_message, list_contact_messages, patch_contact_status

router = APIRouter(tags=["Contact"])

# Public
@router.post("/contact", response_model=ContactOut, status_code=201)
def contact(payload: ContactCreateIn, 
            request : Request,
            db: Session = Depends(get_db),
            _: bool = Depends(rate_limit_contact),
            ):
    return create_contact_message(db, payload.email, payload.title, payload.description)

# Admin list
@router.get("/admin/messages", response_model=list[ContactOut])
def admin_list_messages(
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    return list_contact_messages(db)

# Admin patch status
@router.patch("/admin/messages/{message_id}/status", response_model=ContactOut)
def admin_patch_message_status(
    message_id: int,
    payload: ContactStatusPatchIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    return patch_contact_status(db, message_id, payload.status)
