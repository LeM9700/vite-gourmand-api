from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError

from app.core.db_postgres import get_db
from app.modules.menus.models_dishes import Dish, DishAllergen, DishType
from app.modules.menus.schemas import DishOut, DishCreateIn, DishUpdateIn, DishAllergensReplaceIn
from app.modules.auth.deps import require_employee_or_admin

router = APIRouter(prefix="/dishes", tags=["Dishes"])

def normalize_allergens(allergens: list[str]) -> list[str]:
    cleaned = []
    seen = set()

    for a in allergens:
        a_clean = a.strip()
        if not a_clean:
            continue

        key = a_clean.lower()
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(a_clean.capitalize())

    return cleaned

@router.post("", response_model=DishOut, status_code=201)
def create_dish(
    payload: DishCreateIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    dish = Dish(
        name=payload.name,
        dish_type=payload.dish_type,
        description=payload.description,
    )

    db.add(dish)
    db.flush()  # récupère dish.id sans commit

    allergens = normalize_allergens(payload.allergens)
    for allergen in allergens:
        db.add(DishAllergen(dish_id=dish.id, allergen=allergen))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Plat déjà existant")

    db.refresh(dish)
    return dish

@router.get("", response_model=list[DishOut])
def list_dishes(
    db: Session = Depends(get_db),
    dish_type: DishType | None = Query(default=None), 
    search: str | None = Query(default=None, min_length=1),
    allergen: str | None = Query(default=None, min_length=1),
):
    stmt = select(Dish)

    if dish_type:
        stmt = stmt.where(Dish.dish_type == dish_type)

    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(
            Dish.name.ilike(like),
            Dish.description.ilike(like),
        ))

    if allergen:
        a = allergen.strip().lower()
        stmt = stmt.join(DishAllergen, DishAllergen.dish_id == Dish.id)
        stmt = stmt.where(func.lower(func.trim(DishAllergen.allergen)) == a)

    stmt = stmt.order_by(Dish.id.asc())

    return db.execute(stmt).scalars().all()


@router.get("/{dish_id}", response_model=DishOut)
def get_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = db.execute(
        select(Dish).where(Dish.id == dish_id)
    ).scalar_one_or_none()

    if dish is None:
        raise HTTPException(status_code=404, detail="Plat introuvable")

    return dish



@router.patch("/{dish_id}", response_model=DishOut)
def update_dish(
    dish_id: int,
    payload: DishUpdateIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    dish = db.execute(select(Dish).where(Dish.id == dish_id)).scalar_one_or_none()
    if dish is None:
        raise HTTPException(status_code=404, detail="Plat introuvable")

    data = payload.model_dump(exclude_unset=True, exclude={"allergens"})
    for field, value in data.items():
        setattr(dish, field, value)

    if payload.allergens is not None:
        db.query(DishAllergen).filter(DishAllergen.dish_id == dish_id).delete()
        for allergen in normalize_allergens(payload.allergens):
            db.add(DishAllergen(dish_id=dish_id, allergen=allergen))

    db.commit()
    db.refresh(dish)
    return dish


@router.put("/{dish_id}/allergens", response_model=DishOut)
def replace_dish_allergens(
    dish_id: int,
    payload: DishAllergensReplaceIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    dish = db.execute(select(Dish).where(Dish.id == dish_id)).scalar_one_or_none()
    if dish is None:
        raise HTTPException(status_code=404, detail="Plat introuvable")

    db.query(DishAllergen).filter(DishAllergen.dish_id == dish_id).delete()

    for allergen in normalize_allergens(payload.allergens):
        db.add(DishAllergen(dish_id=dish_id, allergen=allergen))

    db.commit()
    db.refresh(dish)
    return dish


@router.delete("/{dish_id}", status_code=204)
def delete_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    dish = db.execute(select(Dish).where(Dish.id == dish_id)).scalar_one_or_none()
    if dish is None:
        raise HTTPException(status_code=404, detail="Plat introuvable")

    db.delete(dish)
    db.commit()
    return None
