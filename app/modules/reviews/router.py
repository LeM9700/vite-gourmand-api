from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.db_postgres import get_db
from app.modules.auth.deps import get_current_user, require_employee_or_admin
from app.modules.reviews.schemas import ReviewCreateIn, ReviewOut, ReviewModerateIn, ReviewPublicOut, CustomerInfoOut
from app.modules.reviews.service import create_review_for_order, moderate_review, get_approved_reviews

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
    review = moderate_review(
        db=db,
        review_id=review_id,
        moderator_user_id=current_user.id,
        status=payload.status
    )
    
    # Enrichir avec les infos client
    return {
        **ReviewOut.model_validate(review).model_dump(exclude={'customer'}),
        'customer': CustomerInfoOut.model_validate(review.user).model_dump() if review.user else None
    }

@router.get("/reviews/approved", response_model=List[ReviewPublicOut])
def get_approved_reviews_endpoint(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, description="Nombre maximum d'avis à retourner"),
    sort_by: str = Query("date", regex="^(date|rating)$", description="Critère de tri: 'date' ou 'rating'"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri: 'asc' ou 'desc'")
):
    """
    Récupère les avis approuvés avec options de tri et limitation.
    
    - **limit**: Limite le nombre d'avis retournés (optionnel)
    - **sort_by**: Trie par 'date' (création) ou 'rating' (note)
    - **order**: Ordre 'asc' (croissant) ou 'desc' (décroissant)
    """
    reviews = get_approved_reviews(
        db=db,
        limit=limit,
        sort_by=sort_by,
        order=order
    )
    
    # Construire la réponse enrichie avec le nom du client
    result = []
    for review in reviews:
        review_dict = {
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at,
            'customer_name': f"{review.user.firstname} {review.user.lastname}" if review.user else "Client"
        }
        result.append(review_dict)
    
    return result

@router.get("/reviews/all", response_model=List[ReviewOut])
def get_all_reviews_for_moderation(
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
    limit: Optional[int] = Query(None, ge=1, description="Nombre maximum d'avis à retourner"),
    sort_by: str = Query("date", regex="^(date|rating)$", description="Critère de tri: 'date' ou 'rating'"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri: 'asc' ou 'desc'")
):
    """
    Récupère TOUS les avis (incluant pending/rejected) pour la modération.
    Accès réservé aux employés/admins.
    """
    from sqlalchemy import select, desc, asc
    from sqlalchemy.orm import joinedload
    from app.modules.reviews.models import Review
    
    # Construction de la requête avec eager loading
    stmt = select(Review).options(
        joinedload(Review.user),
        joinedload(Review.order)
    )
    
    # Ajout du tri
    if sort_by == "date":
        stmt = stmt.order_by(desc(Review.created_at) if order == "desc" else asc(Review.created_at))
    else:
        stmt = stmt.order_by(
            desc(Review.rating) if order == "desc" else asc(Review.rating),
            desc(Review.created_at)
        )
    
    # Ajout de la limite
    if limit is not None:
        stmt = stmt.limit(limit)
    
    reviews = db.execute(stmt).scalars().unique().all()
    
    # Construire la réponse enrichie
    result = []
    for review in reviews:
        review_dict = ReviewOut.model_validate(review).model_dump(exclude={'customer'})
        review_dict['customer'] = CustomerInfoOut.model_validate(review.user).model_dump() if review.user else None
        result.append(review_dict)
    
    return result