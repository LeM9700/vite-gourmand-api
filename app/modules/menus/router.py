from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select,or_,and_,func
import re

from decimal import Decimal

from app.core.db_postgres import get_db
from app.modules.menus.models import Menu
from app.modules.menus.models_images import MenuImage
from app.modules.menus.models_dishes import Dish, MenuDish
from app.modules.menus.schemas import MenuListOut , MenuOut, MenuDetailOut, MenuStockPatchIn, MenuCreateIn, MenuImageCreateIn, MenuImageOut, MenuUpdateIn, MenuSearchListOut,MenuSearchOut
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

@router.get("/search", response_model=MenuSearchListOut)
def search_menus(
    db: Session = Depends(get_db),
    q: str = Query(default="", min_length=0, description="Terme de recherche (vide = tous les menus)"),
    active_only: bool = Query(default=True, description="Rechercher seulement dans les menus actifs"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre maximum de résultats")
):
    """
    Recherche dans les menus par:
    - Titre du menu
    - Thème du menu  
    - Régime du menu
    - Nom des plats associés
    """
    if not q or q.strip() == "":
        # Utiliser la même logique que list_menus mais avec le format search
        stmt = select(Menu)
        if active_only:
            stmt = stmt.where(Menu.is_active.is_(True))
        stmt = stmt.order_by(Menu.id.asc()).limit(limit)
        
        menus = db.execute(stmt).scalars().all()
        results = []
        
        for menu in menus:
            result = MenuSearchOut(
                id=menu.id,
                title=menu.title,
                description=menu.description,
                theme=menu.theme,
                regime=menu.regime,
                min_people=menu.min_people,
                base_price=menu.base_price,
                stock=menu.stock,
                is_active=menu.is_active,
                match_source="all",  # ✅ Indique que c'est un listing complet
                matched_dish_names=[],
                images=menu.images,
                dishes=menu.dishes
            )
            results.append(result)
        
        return MenuSearchListOut(
            items=results,
            total_count=len(results),
            search_term=""
        )
    
    
    # ✅ Validation pour les vraies recherches (2+ caractères)
    if len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La recherche doit contenir au moins 2 caractères"
        )
    
    if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\-_.]+$', q):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caractères non autorisés dans la recherche"
        )
    
    # Échappement des caractères SQL wildcards
    clean_q = q.replace('%', '\\%').replace('_', '\\_')
    search_term = f"%{clean_q.lower()}%"
    
    
    # Recherche dans les titres, thèmes et régimes de menus
    menu_stmt = select(Menu).where(
        and_(
            Menu.is_active.is_(True) if active_only else True,
            or_(
                func.lower(Menu.title).like(search_term),
                func.lower(Menu.theme).like(search_term),
                func.lower(Menu.regime).like(search_term)
            )
        )
    ).limit(limit)
    
    menu_results = db.execute(menu_stmt).scalars().all()
    
    # Recherche dans les noms de plats
    dish_stmt = select(Menu).join(MenuDish).join(Dish).where(
        and_(
            Menu.is_active.is_(True) if active_only else True,
            func.lower(Dish.name).like(search_term)
        )
    ).limit(limit)
    
    dish_menu_results = db.execute(dish_stmt).scalars().all()
    
    # Combiner les résultats et éviter les doublons
    all_menus = {}
    results = []
    
    # Traiter les résultats des menus
    for menu in menu_results:
        if menu.id not in all_menus:
            all_menus[menu.id] = menu
            
            # Déterminer la source du match
            match_source = "title"
            if q.lower() in menu.theme.lower():
                match_source = "theme"
            elif q.lower() in menu.regime.lower():
                match_source = "regime"
                
            result = MenuSearchOut(
                id=menu.id,
                title=menu.title,
                description=menu.description,
                theme=menu.theme,
                regime=menu.regime,
                min_people=menu.min_people,
                base_price=menu.base_price,
                stock=menu.stock,
                is_active=menu.is_active,
                match_source=match_source,
                matched_dish_names=[],
                images=menu.images,
                dishes=menu.dishes
            )
            results.append(result)
    
    # Traiter les résultats des plats
    for menu in dish_menu_results:
        matched_dishes = [
            dish.name for dish in menu.dishes 
            if q.lower() in dish.name.lower()
        ]
        
        if menu.id not in all_menus:
            all_menus[menu.id] = menu
            result = MenuSearchOut(
                id=menu.id,
                title=menu.title,
                description=menu.description,
                theme=menu.theme,
                regime=menu.regime,
                min_people=menu.min_people,
                base_price=menu.base_price,
                stock=menu.stock,
                is_active=menu.is_active,
                match_source="dish",
                matched_dish_names=matched_dishes,
                images=menu.images,
                dishes=menu.dishes
            )
            results.append(result)
        else:
            # Menu déjà trouvé par titre/thème/régime, ajouter les plats matchés
            for result in results:
                if result.id == menu.id:
                    if not result.matched_dish_names:
                        result.matched_dish_names = matched_dishes
                    break
    
    # Trier par pertinence (titre exact > thème/régime > plats)
    results.sort(key=lambda x: (
        0 if x.match_source == "title" else
        1 if x.match_source in ["theme", "regime"] else 2
    ))
    
    return MenuSearchListOut(
        items=results,
        total_count=len(results),
        search_term=q
    )



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
    
    # Ajouter les plats
    for dish_id in payload.dish_ids:
        dish = db.execute(select(Dish).where(Dish.id == dish_id)).scalar_one_or_none()
        if dish is None:
            raise HTTPException(status_code=404, detail=f"Plat {dish_id} introuvable")
        db.add(MenuDish(menu_id=menu.id, dish_id=dish_id))
    
    # Ajouter les images
    for idx, url in enumerate(payload.image_urls):
        db.add(MenuImage(
            menu_id=menu.id,
            url=url,
            alt_text=menu.title,
            sort_order=idx
        ))
    
    if payload.dish_ids or payload.image_urls:
        db.commit()
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

    data = payload.model_dump(exclude_unset=True, exclude={"dish_ids", "image_urls"})

    for field, value in data.items():
        setattr(menu, field, value)
    
    # Mise à jour des plats si fourni
    if payload.dish_ids is not None:
        # Supprimer les anciennes associations
        db.query(MenuDish).filter(MenuDish.menu_id == menu_id).delete()
        
        # Ajouter les nouvelles associations
        for dish_id in payload.dish_ids:
            dish = db.execute(select(Dish).where(Dish.id == dish_id)).scalar_one_or_none()
            if dish is None:
                raise HTTPException(status_code=404, detail=f"Plat {dish_id} introuvable")
            db.add(MenuDish(menu_id=menu_id, dish_id=dish_id))
    
    # Mise à jour des images si fourni
    if payload.image_urls is not None:
        # Supprimer les anciennes images
        db.query(MenuImage).filter(MenuImage.menu_id == menu_id).delete()
        
        # Ajouter les nouvelles images
        for idx, url in enumerate(payload.image_urls):
            db.add(MenuImage(
                menu_id=menu_id,
                url=url,
                alt_text=menu.title,
                sort_order=idx
            ))

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
