from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.orders.models import Order
from app.modules.reviews.models import Review

ALLOWED_ORDER_STATUSES_FOR_REVIEW = {"DELIVERED", "COMPLETED"}
ALLOWED_REVIEW_STATUSES = {"APPROVED", "REJECTED"}

def create_review_for_order(db: Session, order_id: int, user_id: int, rating: int, comment: str) -> Review:
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    if order.status not in ALLOWED_ORDER_STATUSES_FOR_REVIEW:
        raise HTTPException(status_code=400, detail="Avis autorisé uniquement après livraison")

    review = Review(order_id=order_id, user_id=user_id, rating=rating, comment=comment, status="PENDING")
    db.add(review)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Avis déjà existant pour cette commande")

    db.refresh(review)
    return review

def moderate_review(db: Session, review_id: int, moderator_user_id: int, status: str) -> Review:
    if status not in ALLOWED_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="Statut invalide (APPROVED/REJECTED)")

    review = db.execute(select(Review).where(Review.id == review_id)).scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Avis introuvable")

    review.status = status
    review.moderated_by_user_id = moderator_user_id
    review.moderated_at = datetime.now(timezone.utc)

    db.add(review)
    db.commit()
    db.refresh(review)
    return review
