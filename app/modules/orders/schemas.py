from datetime import date, time, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class OrderCreateIn(BaseModel):
    menu_id: int
    event_address: str = Field(min_length=5)
    event_city: str = Field(min_length=2, max_length=120)
    event_date: date
    event_time: time

    delivery_km: Decimal = Field(ge=0)
    people_count: int = Field(ge=1)
    has_loaned_equipment: bool = False

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    menu_id: int

    event_address: str
    event_city: str
    event_date: date
    event_time: time

    delivery_km: Decimal
    delivery_fee: Decimal

    people_count: int
    menu_price: Decimal
    discount: Decimal
    total_price: Decimal

    status: str
    has_loaned_equipment: bool


# Schémas pour les relations
class UserInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    firstname: str
    lastname: str
    email: str
    phone: str
    address: str

class MenuInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    base_price: Decimal
    min_people: int

# OrderOut enrichi avec customer et menu
class OrderWithDetailsOut(OrderOut):
    customer: UserInfoOut | None = None
    menu: MenuInfoOut | None = None


class OrderHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    changed_at: datetime
    changed_by_user_id: int | None = None
    note: str | None = None

class OrderDetailOut(OrderOut):
    history: list[OrderHistoryOut] = []
    customer: UserInfoOut | None = None
    menu: MenuInfoOut | None = None

class OrderListOut(BaseModel):
    items: list[OrderWithDetailsOut]
    
class OrderStatusPatchIn(BaseModel):
    status: str = Field(min_length=3, max_length=30)
    note: str | None = None    
    
class OrderCancelIn(BaseModel):
    contact_mode: str = Field(min_length=3, max_length=20)  # EMAIL/PHONE
    reason: str = Field(min_length=5)
    


class OrderUpdateIn(BaseModel):
    people_count: int | None = Field(default=None, gt=0)
    event_address: str | None = None
    event_city: str | None = None
    event_date: date | None = None
    event_time: time | None = None
    delivery_km: int | None = Field(default=None, ge=0)
    has_loaned_equipment: bool | None = None