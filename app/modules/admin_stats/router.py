from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.db_postgres import get_db
from app.core.db_mongo import get_mongo_db
from app.modules.auth.deps import require_admin
from app.modules.admin_stats.service import (
    recompute_menu_daily_stats,
    get_orders_by_menu_stats,
    get_revenue_by_menu_stats,
    get_menu_comparison_stats,
    get_dashboard_kpi
)
from app.modules.admin_stats.schemas import (
    OrdersByMenuResponse,
    RevenueByMenuResponse,
    MenuComparisonResponse,
    DashboardKpiResponse
)

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])


@router.post("/recompute")
def recompute(day: date = Query(...), db: Session = Depends(get_db), _admin = Depends(require_admin)):
    """
    Recalcule les statistiques journalières pour un jour donné.
    Utile pour corriger des données ou après modification de commandes.
    """
    mongo_db = get_mongo_db()
    return recompute_menu_daily_stats(db=db, mongo_db=mongo_db, day=day)


@router.get("/menus/daily")
def get_daily(day: date = Query(...), _admin = Depends(require_admin)):
    """
    Récupère les statistiques quotidiennes brutes pour un jour donné.
    Format original de la collection MongoDB.
    """
    mongo_db = get_mongo_db()
    docs = list(mongo_db["menu_stats_daily"].find({"day": day.isoformat()}, {"_id": 0}))
    return {"day": day.isoformat(), "items": docs}


@router.get("/orders-by-menu", response_model=OrdersByMenuResponse)
def get_orders_by_menu(
    start_date: date = Query(..., description="Date de début (incluse)"),
    end_date: date = Query(..., description="Date de fin (incluse)"),
    menu_id: Optional[int] = Query(None, description="Filtrer sur un menu spécifique"),
    _admin = Depends(require_admin)
):
    """
    📊 **Statistiques de commandes par menu sur une période**
    
    Permet de :
    - Comparer le nombre de commandes entre différents menus
    - Voir le CA généré par chaque menu
    - Identifier les menus les plus populaires
    - Calculer la valeur moyenne des commandes
    
    **Filtres :**
    - `start_date` / `end_date` : Période d'analyse (custom range)
    - `menu_id` : Optionnel, pour analyser un seul menu
    
    **Cas d'usage :**
    - Graphique bar chart comparant les menus
    - Dashboard avec indicateurs clés
    - Analyse de performance commerciale
    """
    mongo_db = get_mongo_db()
    return get_orders_by_menu_stats(
        mongo_db=mongo_db,
        start_date=start_date,
        end_date=end_date,
        menu_id=menu_id
    )


@router.get("/revenue-by-menu", response_model=RevenueByMenuResponse)
def get_revenue_by_menu(
    start_date: date = Query(..., description="Date de début (incluse)"),
    end_date: date = Query(..., description="Date de fin (incluse)"),
    menu_ids: Optional[List[int]] = Query(None, description="Liste d'IDs de menus à analyser"),
    _admin = Depends(require_admin)
):
    """
    💰 **Chiffre d'affaires détaillé par menu**
    
    Calcule le CA sur une période avec statistiques avancées :
    - CA total et nombre de commandes
    - Valeur moyenne par commande
    - Meilleur jour de vente (date + montant)
    
    **Filtres :**
    - `start_date` / `end_date` : Période d'analyse
    - `menu_ids` : Liste de menus à comparer (vide = tous les menus)
    
    **Cas d'usage :**
    - Tableau de bord CA avec filtres
    - Graphique line chart d'évolution du CA
    - Export Excel pour comptabilité
    - Identification des meilleurs performers
    """
    mongo_db = get_mongo_db()
    return get_revenue_by_menu_stats(
        mongo_db=mongo_db,
        start_date=start_date,
        end_date=end_date,
        menu_ids=menu_ids
    )


@router.get("/comparison", response_model=MenuComparisonResponse)
def get_menu_comparison(
    start_date: date = Query(..., description="Date de début (incluse)"),
    end_date: date = Query(..., description="Date de fin (incluse)"),
    _admin = Depends(require_admin)
):
    """
    📈 **Comparaison complète entre tous les menus**
    
    Données agrégées pour graphiques interactifs :
    - Nombre de commandes par menu
    - Chiffre d'affaires par menu
    - Note moyenne (avg_rating)
    - Nombre d'avis clients
    
    **Idéal pour :**
    - Bar chart comparant les performances
    - Pie chart de répartition du CA
    - Graphiques multi-axes (commandes + CA + notes)
    - Switch entre différents types de visualisation
    
    **Types de graphiques possibles :**
    - Bar chart (vertical/horizontal)
    - Line chart (évolution)
    - Pie/Donut chart (parts de marché)
    - Radar chart (multi-critères)
    """
    mongo_db = get_mongo_db()
    return get_menu_comparison_stats(
        mongo_db=mongo_db,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/dashboard/kpi", response_model=DashboardKpiResponse)
def get_kpi(
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    """
    Récupère les KPI du dashboard admin pour le jour actuel.
    
    **Retourne :**
    - total_orders_today : Nombre de commandes avec event_date aujourd'hui
    - total_revenue_today : CA total des commandes d'aujourd'hui
    - pending_orders : Commandes en attente (status PLACED ou ACCEPTED)
    - active_employees : Nombre d'employés actifs
    - pending_reviews : Avis en attente de modération (status PENDING)
    - pending_messages : Messages de contact non traités (status SENT)
    """
    return get_dashboard_kpi(db=db)
