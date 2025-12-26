from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

class MenuDailyStatOut(BaseModel):
    day: date
    menu_id: int
    orders_count: int
    revenue_total: Decimal
    reviews_count: int
    avg_rating: float | None = None
    updated_at: datetime
