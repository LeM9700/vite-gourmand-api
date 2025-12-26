from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.core.db_postgres import get_db
from app.modules.auth.deps import get_current_user,require_employee_or_admin
from app.modules.orders.schemas import OrderCreateIn, OrderHistoryOut, OrderOut, OrderDetailOut, OrderListOut, OrderStatusPatchIn, OrderCancelIn
from app.modules.orders.service import create_order, list_my_orders, get_order_detail_for_user, list_orders_admin, patch_order_status, cancel_order

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderOut, status_code=201)
def place_order(
    payload: OrderCreateIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    order = create_order(db=db, user_id=current_user.id, payload=payload)
    return order


@router.get("/me", response_model=OrderListOut)
def my_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    orders = list_my_orders(db=db, user_id=current_user.id)
    return {"items": orders}


@router.get("/{order_id}", response_model=OrderDetailOut)
def order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    order, history = get_order_detail_for_user(db=db, order_id=order_id, user_id=current_user.id)

    return {
        **OrderOut.model_validate(order).model_dump(),
        "history": [OrderHistoryOut.model_validate(h).model_dump() for h in history],
    }
    
 
@router.get("", response_model=OrderListOut)
def list_orders(
    db: Session = Depends(get_db),
    _user = Depends(require_employee_or_admin),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    city: str | None = Query(default=None),
):
    orders = list_orders_admin(
        db=db, status=status, date_from=date_from, date_to=date_to, city=city
    )
    return {"items": orders}   


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusPatchIn,
    db: Session = Depends(get_db),
    current_user = Depends(require_employee_or_admin),
):
    order = patch_order_status(
        db=db,
        order_id=order_id,
        new_status=payload.status,
        changed_by_user_id=current_user.id,
        note=payload.note,
    )
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order_endpoint(
    order_id: int,
    payload: OrderCancelIn,
    db: Session = Depends(get_db),
    current_user = Depends(require_employee_or_admin),
):
    order = cancel_order(
        db=db,
        order_id=order_id,
        cancelled_by_user_id=current_user.id,
        contact_mode=payload.contact_mode,
        reason=payload.reason
    )
    return order
