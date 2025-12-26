from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_base import Base

class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    dish_type: Mapped[str] = mapped_column(String(20), nullable=False)  # STARTER/MAIN/DESSERT
    description: Mapped[str] = mapped_column(Text, nullable=False)
    allergens = relationship(
    "DishAllergen",
    primaryjoin="Dish.id==DishAllergen.dish_id",
    cascade="all, delete-orphan",
    lazy="selectin"
)


class DishAllergen(Base):
    __tablename__ = "dish_allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    allergen: Mapped[str] = mapped_column(String(80), nullable=False)

class MenuDish(Base):
    __tablename__ = "menu_dishes"

    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id", ondelete="CASCADE"), primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="RESTRICT"), primary_key=True)
