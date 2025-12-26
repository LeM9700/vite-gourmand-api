from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Numeric, Integer, String, Text, Time, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="RESTRICT"), nullable=False)

    event_address: Mapped[str] = mapped_column(Text, nullable=False)
    event_city: Mapped[str] = mapped_column(String(120), nullable=False)
    event_date: Mapped["Date"] = mapped_column(Date, nullable=False)
    event_time: Mapped["Time"] = mapped_column(Time, nullable=False)

    delivery_km: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    people_count: Mapped[int] = mapped_column(Integer, nullable=False)
    menu_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PLACED")
    has_loaned_equipment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class OrderCancellation(Base):
    __tablename__ = "order_cancellations"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    cancelled_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    contact_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # EMAIL/PHONE
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
