from sqlalchemy import Boolean, Integer, Numeric, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_base import Base

class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(String(50), nullable=False)
    regime: Mapped[str] = mapped_column(String(50), nullable=False)

    min_people: Mapped[int] = mapped_column(Integer, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    conditions_text: Mapped[str] = mapped_column(Text, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    images = relationship(
        "MenuImage",
        primaryjoin="Menu.id==MenuImage.menu_id",
        order_by="MenuImage.sort_order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    dishes = relationship(
        "Dish",
        secondary="menu_dishes",
        lazy="selectin"
    )