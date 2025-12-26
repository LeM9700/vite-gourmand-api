from datetime import date as date_type
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select,desc
from sqlalchemy.exc import IntegrityError

from app.modules.menus.models import Menu
from app.modules.orders.models import Order, OrderStatusHistory, OrderCancellation


DELIVERY_BASE_FEE = Decimal("5.00")
DELIVERY_PER_KM = Decimal("0.59")


def _money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_order(db: Session, user_id: int, payload) -> Order:
    # 1) menu existe + actif
    menu = db.execute(select(Menu).where(Menu.id == payload.menu_id)).scalar_one_or_none()
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    if not menu.is_active:
        raise HTTPException(status_code=400, detail="Menu désactivé")

    # 2) date dans le futur (réaliste)
    if payload.event_date <= date_type.today():
        raise HTTPException(status_code=400, detail="La date de l'évènement doit être dans le futur")

    # 3) min_people
    if payload.people_count < menu.min_people:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum {menu.min_people} personnes pour ce menu"
        )

    # 4) stock : 1 commande = 1 stock
    if menu.stock <= 0:
        raise HTTPException(status_code=400, detail="Menu en rupture de stock")

    # 5) calcul prix (serveur)
    delivery_fee = _money(DELIVERY_BASE_FEE + (Decimal(payload.delivery_km) * DELIVERY_PER_KM))
    menu_price = _money(Decimal(menu.base_price))
    discount = Decimal("0.00")
    total_price = _money(menu_price*payload.people_count + delivery_fee - discount)

    # 6) décrémenter stock
    menu.stock -= 1
    db.add(menu)

    # 7) créer order
    order = Order(
        user_id=user_id,
        menu_id=payload.menu_id,
        event_address=payload.event_address,
        event_city=payload.event_city,
        event_date=payload.event_date,
        event_time=payload.event_time,
        delivery_km=_money(Decimal(payload.delivery_km)),
        delivery_fee=delivery_fee,
        people_count=payload.people_count,
        menu_price=menu_price,
        discount=discount,
        total_price=total_price,
        status="PLACED",
        has_loaned_equipment=payload.has_loaned_equipment,
    )
    db.add(order)
    db.flush()  # récupère order.id sans commit

    # 8) history
    hist = OrderStatusHistory(
        order_id=order.id,
        status="PLACED",
        changed_by_user_id=user_id,
        note="Commande créée"
    )
    db.add(hist)

    # 9) commit transaction
    db.commit()
    db.refresh(order)
    return order

def list_my_orders(db: Session, user_id: int) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(desc(Order.created_at))
    )
    return db.execute(stmt).scalars().all()

def get_order_detail_for_user(db: Session, order_id: int, user_id: int):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    history = db.execute(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order_id)
        .order_by(OrderStatusHistory.changed_at.asc())
    ).scalars().all()

    return order, history


ALLOWED_TRANSITIONS = {
    "PLACED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PREPARING", "CANCELLED"},
    "PREPARING": {"DELIVERING"},
    "DELIVERING": {"DELIVERED"},
    "DELIVERED": {"WAITING_RETURN", "COMPLETED"},
    "WAITING_RETURN": {"COMPLETED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}

def list_orders_admin(
    db: Session,
    status: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    city: str | None = None,
):
    stmt = select(Order)

    if status:
        stmt = stmt.where(Order.status == status)

    if city:
        stmt = stmt.where(Order.event_city == city)

    if date_from:
        stmt = stmt.where(Order.event_date >= date_from)

    if date_to:
        stmt = stmt.where(Order.event_date <= date_to)

    stmt = stmt.order_by(desc(Order.created_at))
    return db.execute(stmt).scalars().all()


def patch_order_status(
    db: Session,
    order_id: int,
    new_status: str,
    changed_by_user_id: int,
    note: str | None,
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    current = order.status

    # Règle réaliste : DELIVERED -> WAITING_RETURN seulement si matériel prêté
    if current == "DELIVERED" and new_status == "WAITING_RETURN" and not order.has_loaned_equipment:
        raise HTTPException(status_code=400, detail="Aucun matériel prêté : passage WAITING_RETURN interdit")

    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Transition interdite: {current} → {new_status}")

    order.status = new_status
    db.add(order)

    hist = OrderStatusHistory(
        order_id=order.id,
        status=new_status,
        changed_by_user_id=changed_by_user_id,
        note=note
    )
    db.add(hist)

    db.commit()
    db.refresh(order)
    return order


NON_REFUNDABLE_STATUSES = {"DELIVERING", "DELIVERED", "WAITING_RETURN", "COMPLETED"}

def cancel_order(
    db: Session,
    order_id: int,
    cancelled_by_user_id: int,
    contact_mode: str,
    reason: str,
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    if order.status in ("CANCELLED", "COMPLETED"):
        raise HTTPException(status_code=400, detail="Commande non annulable")

    # Valider contact_mode (simple)
    if contact_mode not in ("EMAIL", "PHONE"):
        raise HTTPException(status_code=400, detail="contact_mode invalide (EMAIL/PHONE)")

    # Recrédit stock si pas trop tard
    if order.status not in NON_REFUNDABLE_STATUSES:
        menu = db.execute(select(Menu).where(Menu.id == order.menu_id)).scalar_one_or_none()
        if menu is not None:
            menu.stock += 1
            db.add(menu)

    # Statut CANCELLED + history
    order.status = "CANCELLED"
    db.add(order)

    hist = OrderStatusHistory(
        order_id=order.id,
        status="CANCELLED",
        changed_by_user_id=cancelled_by_user_id,
        note=f"Annulation ({contact_mode}) - {reason}"
    )
    db.add(hist)

    cancellation = OrderCancellation(
        order_id=order.id,
        cancelled_by_user_id=cancelled_by_user_id,
        contact_mode=contact_mode,
        reason=reason
    )
    db.add(cancellation)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Unique(order_id) -> déjà annulée / déjà enregistrée
        raise HTTPException(status_code=409, detail="Annulation déjà enregistrée pour cette commande")

    db.refresh(order)
    return order