from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db_postgres import get_db
from app.modules.auth.deps import get_current_user, require_employee_or_admin
from app.modules.reviews.schemas import ReviewCreateIn, ReviewOut, ReviewModerateIn
from app.modules.reviews.service import create_review_for_order, moderate_review

router = APIRouter(tags=["Reviews"])

@router.post("/orders/{order_id}/review", response_model=ReviewOut, status_code=201)
def create_review_endpoint(
    order_id: int,
    payload: ReviewCreateIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return create_review_for_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment
    )

@router.patch("/reviews/{review_id}/moderate", response_model=ReviewOut)
def moderate_review_endpoint(
    review_id: int,
    payload: ReviewModerateIn,
    db: Session = Depends(get_db),
    current_user = Depends(require_employee_or_admin),
):
    return moderate_review(
        db=db,
        review_id=review_id,
        moderator_user_id=current_user.id,
        status=payload.status
    )
