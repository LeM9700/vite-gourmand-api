from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from app.modules.menus.models_dishes import DishType


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
    dish_type: DishType
    description: str
    allergens: list[DishAllergenOut] = []
    
        
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
    
    # Relations pour l'affichage complet
    images: list["MenuImageOut"] = []
    dishes: list["DishOut"] = []

class MenuListOut(BaseModel):
    items: list[MenuOut]





    
# --- DISH INPUTS ---

class DishCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    dish_type: DishType = Field()
    description: str = Field(min_length=5)
    allergens: list[str] = []


class DishUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    dish_type: DishType | None = Field(default=None)
    description: str | None = Field(default=None, min_length=5)
    allergens: list[str] | None = None


class DishAllergensReplaceIn(BaseModel):
    allergens: list[str]
        



class MenuDetailOut(BaseModel):
    """Schéma complet pour le détail d'un menu avec images et plats"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str
    theme: str
    regime: str
    min_people: int
    base_price: Decimal
    conditions_text: str
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Relations
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
    
    dish_ids: List[int] = []
    image_urls: List[str] = []    
    
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
    
    dish_ids: Optional[List[int]] = None
    image_urls: Optional[List[str]] = None   
    
    

class MenuSearchOut(BaseModel):
    """Schema pour les résultats de recherche avec highlight des termes trouvés"""
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
    
    # Champs pour indiquer où la recherche a matché
    match_source: str  # "title", "theme", "regime", "dish"
    matched_dish_names: List[str] = []  # Si match sur des plats
    
    images: List["MenuImageOut"] = []
    dishes: List["DishOut"] = []

class MenuSearchListOut(BaseModel):
    items: List[MenuSearchOut]
    total_count: int
    search_term: str