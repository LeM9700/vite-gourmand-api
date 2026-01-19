from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, asc
from typing import List, Optional
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



def get_approved_reviews(
    db: Session, 
    limit: Optional[int] = None, 
    sort_by: str = "date", 
    order: str = "desc"
) -> List[Review]:
    """
    Récupère les avis approuvés avec options de tri et limitation
    
    Args:
        db: Session de base de données
        limit: Nombre maximum d'avis à retourner (None = pas de limite)
        sort_by: Critère de tri ("date" ou "rating")
        order: Ordre de tri ("asc" ou "desc")
    """
    # Validation des paramètres
    if sort_by not in ["date", "rating"]:
        raise HTTPException(status_code=400, detail="sort_by doit être 'date' ou 'rating'")
    
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order doit être 'asc' ou 'desc'")
    
    if limit is not None and limit <= 0:
        raise HTTPException(status_code=400, detail="limit doit être supérieur à 0")
    
    # Construction de la requête avec eager loading
    stmt = select(Review).options(
        joinedload(Review.user),
        joinedload(Review.order)
    ).where(Review.status == "APPROVED")
    
    # Ajout du tri
    if sort_by == "date":
        if order == "desc":
            stmt = stmt.order_by(desc(Review.created_at))
        else:
            stmt = stmt.order_by(asc(Review.created_at))
    else:  # sort_by == "rating"
        if order == "desc":
            stmt = stmt.order_by(desc(Review.rating), desc(Review.created_at))  # Tri secondaire par date
        else:
            stmt = stmt.order_by(asc(Review.rating), desc(Review.created_at))   # Tri secondaire par date
    
    # Ajout de la limite
    if limit is not None:
        stmt = stmt.limit(limit)
    
    # Exécution de la requête
    reviews = db.execute(stmt).scalars().unique().all()
    return list(reviews)