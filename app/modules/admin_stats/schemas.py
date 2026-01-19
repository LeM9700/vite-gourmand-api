from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

class MenuDailyStatOut(BaseModel):
    day: date
    menu_id: int
    orders_count: int
    revenue_total: Decimal
    reviews_count: int
    avg_rating: float | None = None
    updated_at: datetime


class OrdersByMenuOut(BaseModel):
    """Statistiques de commandes par menu"""
    menu_id: int
    menu_name: Optional[str] = None
    orders_count: int
    total_revenue: float
    avg_order_value: float
    first_order_date: Optional[str] = None
    last_order_date: Optional[str] = None


class OrdersByMenuResponse(BaseModel):
    """Réponse agrégée pour les commandes par menu"""
    start_date: str
    end_date: str
    total_orders: int
    total_revenue: float
    menus: List[OrdersByMenuOut]


class RevenueByMenuOut(BaseModel):
    """Détail du chiffre d'affaires d'un menu"""
    menu_id: int
    menu_name: Optional[str] = None
    period_revenue: float
    orders_count: int
    avg_order_value: float
    best_day_revenue: float
    best_day_date: Optional[str] = None


class RevenueByMenuResponse(BaseModel):
    """Réponse pour le CA par menu avec filtres"""
    start_date: str
    end_date: str
    menu_id: Optional[int] = None
    total_revenue: float
    total_orders: int
    data: List[RevenueByMenuOut]


class MenuComparisonOut(BaseModel):
    """Comparaison entre menus pour graphiques"""
    menu_id: int
    menu_name: Optional[str] = None
    orders_count: int
    revenue: float
    avg_rating: Optional[float] = None
    reviews_count: int


class MenuComparisonResponse(BaseModel):
    """Réponse pour comparaison graphique"""
    start_date: str
    end_date: str
    total_menus: int
    menus: List[MenuComparisonOut]


class DashboardKpiResponse(BaseModel):
    """KPI du dashboard admin pour le jour actuel"""
    total_orders_today: int = Field(description="Nombre total de commandes aujourd'hui")
    total_revenue_today: float = Field(description="Chiffre d'affaires aujourd'hui")
    total_revenue_all_time: float = Field(description="Chiffre d'affaires total (toutes les commandes)")
    pending_orders: int = Field(description="Commandes en attente (PLACED, ACCEPTED)")
    active_employees: int = Field(description="Nombre d'employés actifs")
    pending_reviews: int = Field(description="Avis en attente de modération")
    pending_messages: int = Field(description="Messages de contact non traités")
