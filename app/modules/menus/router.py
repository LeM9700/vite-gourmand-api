from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


from decimal import Decimal

from app.core.db_postgres import get_db
from app.modules.menus.models import Menu
from app.modules.menus.models_images import MenuImage
from app.modules.menus.models_dishes import Dish
from app.modules.menus.schemas import MenuListOut , MenuOut, MenuDetailOut, MenuStockPatchIn, MenuCreateIn, MenuImageCreateIn, MenuImageOut, MenuUpdateIn
from app.modules.auth.deps import require_employee_or_admin

router = APIRouter(prefix="/menus", tags=["Menus"])

@router.get("", response_model=MenuListOut)
def list_menus(
    db: Session = Depends(get_db),
    theme: str | None = Query(default=None),
    regime: str | None = Query(default=None),
    min_people_max: int | None = Query(default=None, ge=1),
    max_price: Decimal | None = Query(default=None, ge=0),
    active_only: bool = Query(default=True),
):
    stmt = select(Menu)

    if active_only:
        stmt = stmt.where(Menu.is_active.is_(True))

    if theme:
        stmt = stmt.where(Menu.theme == theme)

    if regime:
        stmt = stmt.where(Menu.regime == regime)

    if min_people_max is not None:
        stmt = stmt.where(Menu.min_people <= min_people_max)

    if max_price is not None:
        stmt = stmt.where(Menu.base_price <= max_price)

    stmt = stmt.order_by(Menu.id.asc())

    menus = db.execute(stmt).scalars().all()
    return {"items": menus}




@router.get("/{menu_id}", response_model=MenuDetailOut)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    stmt = select(Menu).where(Menu.id == menu_id)
    menu = db.execute(stmt).scalar_one_or_none()

    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    return menu


@router.patch("/{menu_id}/stock")
def update_menu_stock(
    menu_id: int,
    payload: MenuStockPatchIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    stmt = select(Menu).where(Menu.id == menu_id)
    menu = db.execute(stmt).scalar_one_or_none()

    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    menu.stock = payload.stock
    db.add(menu)
    db.commit()
    db.refresh(menu)

    return {"id": menu.id, "stock": menu.stock}


@router.post("", response_model=MenuOut, status_code=201)
def create_menu(
    payload: MenuCreateIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    menu = Menu(
        title=payload.title,
        description=payload.description,
        theme=payload.theme,
        regime=payload.regime,
        min_people=payload.min_people,
        base_price=payload.base_price,
        conditions_text=payload.conditions_text,
        stock=payload.stock,
        is_active=payload.is_active,
    )

    db.add(menu)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, 
            detail="Un menu avec ce titre existe déjà pour ce thème."
        )
    db.refresh(menu)
    return menu


@router.post("/{menu_id}/images", response_model=MenuImageOut, status_code=201)
def add_menu_image(
    menu_id: int,
    payload: MenuImageCreateIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    # 1) vérifier menu existe
    menu = db.execute(select(Menu).where(Menu.id == menu_id)).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    # 2) créer image
    image = MenuImage(
        menu_id=menu_id,
        url=payload.url,
        alt_text=payload.alt_text,
        sort_order=payload.sort_order,
    )

    db.add(image)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cette image existe déjà pour ce menu.")

    db.refresh(image)
    return image

@router.delete("/{menu_id}/images/{image_id}", status_code=204)
def delete_menu_image(
    menu_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    # 1) Vérifier que le menu existe (message clair)
    menu = db.execute(select(Menu).where(Menu.id == menu_id)).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    # 2) Récupérer l'image en s'assurant qu'elle appartient bien à ce menu
    image = db.execute(
        select(MenuImage).where(MenuImage.id == image_id, MenuImage.menu_id == menu_id)
    ).scalar_one_or_none()

    if image is None:
        raise HTTPException(status_code=404, detail="Image introuvable pour ce menu")

    # 3) Supprimer
    db.delete(image)
    db.commit()

    # 204 = no content (pas de body)
    return None


@router.patch("/{menu_id}", response_model=MenuOut)
def update_menu(
    menu_id: int,
    payload: MenuUpdateIn,
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
):
    menu = db.execute(select(Menu).where(Menu.id == menu_id)).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(menu, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Un menu avec ce titre existe déjà pour ce thème."
        )

    db.refresh(menu)
    return menu
