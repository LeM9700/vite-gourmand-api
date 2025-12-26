from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import datetime

class MenuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    theme: str
    regime: str
    min_people: int
    base_price: Decimal
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class MenuListOut(BaseModel):
    items: list[MenuOut]


class MenuImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    alt_text: str
    sort_order: int

class DishAllergenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    allergen: str

class DishOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    dish_type: str
    description: str
    allergens: list[DishAllergenOut] = []

class MenuDetailOut(BaseModel):
    images: list[MenuImageOut] = []
    dishes: list[DishOut] = []
    

class MenuStockPatchIn(BaseModel):
    stock: int = Field(ge=0)    
    
    
class MenuCreateIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10)
    theme: str = Field(min_length=2, max_length=50)
    regime: str = Field(min_length=2, max_length=50)

    min_people: int = Field(ge=1)
    base_price: Decimal = Field(ge=0)

    conditions_text: str = Field(min_length=5)
    stock: int = Field(ge=0, default=0)
    is_active: bool = True    
    
class MenuImageCreateIn(BaseModel):
    url: str = Field(min_length=10)
    alt_text: str = Field(min_length=3, max_length=255)
    sort_order: int = Field(ge=0, default=0)    
    
class MenuImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    alt_text: str
    sort_order: int    
    
 
class MenuUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=10)
    theme: Optional[str] = Field(default=None, min_length=2, max_length=50)
    regime: Optional[str] = Field(default=None, min_length=2, max_length=50)

    min_people: Optional[int] = Field(default=None, ge=1)
    base_price: Optional[Decimal] = Field(default=None, ge=0)

    conditions_text: Optional[str] = Field(default=None, min_length=5)
    stock: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None   