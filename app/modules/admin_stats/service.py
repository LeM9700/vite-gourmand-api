from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, cast, Date as SqlDate
from typing import Optional, List, Dict
from collections import defaultdict
import logging

from app.modules.orders.models import Order
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.modules.contact.models import ContactMessage

logger = logging.getLogger(__name__)


def recompute_menu_daily_stats(db: Session, mongo_db, day: date):
    # 1) Orders agrégées par menu pour ce jour (sur event_date)
    orders_rows = db.execute(
        select(
            Order.menu_id.label("menu_id"),
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Order.total_price), 0).label("revenue_total"),
        )
        .where(Order.event_date == day)
        .group_by(Order.menu_id)
    ).all()

    # 2) Reviews agrégées par menu pour ce jour (sur created_at du review)
    # On récupère les avis créés ce jour-là liés à une commande, via join order_id
    reviews_rows = db.execute(
        select(
            Order.menu_id.label("menu_id"),
            func.count(Review.id).label("reviews_count"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .join(Order, Order.id == Review.order_id)
        .where(cast(Review.created_at, SqlDate) == day)
        .group_by(Order.menu_id)
    ).all()

    reviews_map = {
        r.menu_id: {
            "reviews_count": int(r.reviews_count or 0),
            "avg_rating": float(r.avg_rating) if r.avg_rating is not None else None,
        }
        for r in reviews_rows
    }

    coll = mongo_db["menu_stats_daily"]
    now = datetime.now(timezone.utc)

    # 3) Upsert pour chaque menu présent dans les commandes
    for row in orders_rows:
        menu_id = int(row.menu_id)
        orders_count = int(row.orders_count or 0)
        revenue_total = Decimal(str(row.revenue_total or 0))

        extra = reviews_map.get(menu_id, {"reviews_count": 0, "avg_rating": None})

        coll.update_one(
            {"day": day.isoformat(), "menu_id": menu_id},
            {"$set": {
                "day": day.isoformat(),
                "menu_id": menu_id,
                "orders_count": orders_count,
                "revenue_total": float(revenue_total),  # Mongo stocke en float pour MVP
                "reviews_count": extra["reviews_count"],
                "avg_rating": extra["avg_rating"],
                "updated_at": now,
            }},
            upsert=True
        )

    return {"day": day.isoformat(), "menus_updated": len(orders_rows)}


def get_orders_by_menu_stats(
    mongo_db, 
    start_date: date, 
    end_date: date,
    menu_id: Optional[int] = None
) -> Dict:
    """
    Agrège les statistiques de commandes par menu sur une période.
    Permet de comparer les performances de chaque menu.
    """
    coll = mongo_db["menu_stats_daily"]
    
    # Filtres de base
    match_filter = {
        "day": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }
    
    # Filtre optionnel par menu
    if menu_id is not None:
        match_filter["menu_id"] = menu_id
    
    # Pipeline d'agrégation MongoDB
    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": "$menu_id",
                "orders_count": {"$sum": "$orders_count"},
                "total_revenue": {"$sum": "$revenue_total"},
                "first_order_date": {"$min": "$day"},
                "last_order_date": {"$max": "$day"}
            }
        },
        {
            "$project": {
                "menu_id": "$_id",
                "orders_count": 1,
                "total_revenue": 1,
                "avg_order_value": {
                    "$cond": [
                        {"$eq": ["$orders_count", 0]},
                        0,
                        {"$divide": ["$total_revenue", "$orders_count"]}
                    ]
                },
                "first_order_date": 1,
                "last_order_date": 1,
                "_id": 0
            }
        },
        {"$sort": {"total_revenue": -1}}  # Tri par CA décroissant
    ]
    
    results = list(coll.aggregate(pipeline))
    
    # Calculs globaux
    total_orders = sum(r["orders_count"] for r in results)
    total_revenue = sum(r["total_revenue"] for r in results)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "menus": results
    }


def get_revenue_by_menu_stats(
    mongo_db,
    start_date: date,
    end_date: date,
    menu_ids: Optional[List[int]] = None
) -> Dict:
    """
    Calcul détaillé du chiffre d'affaires par menu avec statistiques avancées.
    Permet de filtrer sur plusieurs menus spécifiques.
    """
    try:
        coll = mongo_db["menu_stats_daily"]
        
        # Filtres
        match_filter = {
            "day": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }
        
        if menu_ids:
            match_filter["menu_id"] = {"$in": menu_ids}
        
        # Agrégation par menu
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": "$menu_id",
                    "period_revenue": {"$sum": "$revenue_total"},
                    "orders_count": {"$sum": "$orders_count"},
                    "days": {
                        "$push": {
                            "day": "$day",
                            "revenue": "$revenue_total"
                        }
                    }
                }
            },
            {
                "$project": {
                    "menu_id": "$_id",
                    "period_revenue": 1,
                    "orders_count": 1,
                    "avg_order_value": {
                        "$cond": [
                            {"$eq": ["$orders_count", 0]},
                            0,
                            {"$divide": ["$period_revenue", "$orders_count"]}
                        ]
                    },
                    "best_day": {
                        "$arrayElemAt": [
                            {
                                "$sortArray": {
                                    "input": "$days",
                                    "sortBy": {"revenue": -1}
                                }
                            },
                            0
                        ]
                    },
                    "_id": 0
                }
            },
            {
                "$project": {
                    "menu_id": 1,
                    "period_revenue": 1,
                    "orders_count": 1,
                    "avg_order_value": 1,
                    "best_day_revenue": "$best_day.revenue",
                    "best_day_date": "$best_day.day"
                }
            },
            {"$sort": {"period_revenue": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        total_revenue = sum(r["period_revenue"] for r in results)
        total_orders = sum(r["orders_count"] for r in results)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "menu_id": menu_ids[0] if menu_ids and len(menu_ids) == 1 else None,
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "data": results
        }
    except Exception as e:
        logger.error(f"❌ Erreur MongoDB dans get_revenue_by_menu_stats: {e}", exc_info=True)
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "menu_id": menu_ids[0] if menu_ids and len(menu_ids) == 1 else None,
            "total_revenue": 0.0,
            "total_orders": 0,
            "data": []
        }


def get_menu_comparison_stats(
    mongo_db,
    start_date: date,
    end_date: date
) -> Dict:
    """
    Comparaison complète entre tous les menus pour les graphiques.
    Inclut commandes, CA, notes moyennes.
    """
    try:
        coll = mongo_db["menu_stats_daily"]
        
        pipeline = [
            {
                "$match": {
                    "day": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": "$menu_id",
                    "orders_count": {"$sum": "$orders_count"},
                    "revenue": {"$sum": "$revenue_total"},
                    "reviews_count": {"$sum": "$reviews_count"},
                    "ratings": {"$push": "$avg_rating"}
                }
            },
            {
                "$project": {
                    "menu_id": "$_id",
                    "orders_count": 1,
                    "revenue": 1,
                    "reviews_count": 1,
                    "avg_rating": {
                        "$avg": {
                            "$filter": {
                                "input": "$ratings",
                                "as": "rating",
                                "cond": {"$ne": ["$$rating", None]}
                            }
                        }
                    },
                    "_id": 0
                }
            },
            {"$sort": {"orders_count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_menus": len(results),
            "menus": results
        }
    except Exception as e:
        logger.error(f"❌ Erreur MongoDB dans get_menu_comparison_stats: {e}", exc_info=True)
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_menus": 0,
            "menus": []
        }


def get_dashboard_kpi(db: Session) -> Dict:
    """
    Récupère les KPI du dashboard admin pour le jour actuel.
    - Total commandes aujourd'hui (sur event_date)
    - CA aujourd'hui
    - Commandes en attente (PLACED, ACCEPTED)
    - Employés actifs
    - Avis en attente de modération
    - Messages de contact non traités
    """
    try:
        from datetime import date
        
        today = date.today()
        
        # 1. Commandes aujourd'hui (event_date = aujourd'hui)
        today_orders = db.execute(
            select(
                func.count(Order.id).label("count"),
                func.coalesce(func.sum(Order.total_price), 0).label("revenue")
            )
            .where(Order.event_date == today)
        ).first()
        
        total_orders_today = int(today_orders.count or 0)
        total_revenue_today = float(today_orders.revenue or 0)
        
        # 2. CA total sur toutes les commandes (tous statuts confondus)
        all_time_revenue = db.execute(
            select(func.coalesce(func.sum(Order.total_price), 0))
        ).scalar() or 0
        total_revenue_all_time = float(all_time_revenue)
        
        # 3. Commandes en attente (status PLACED ou ACCEPTED)
        pending_orders = db.execute(
            select(func.count(Order.id))
            .where(Order.status.in_(["PLACED", "ACCEPTED"]))
        ).scalar() or 0
        
        # 4. Employés actifs (role=EMPLOYEE et is_active=True)
        active_employees = db.execute(
            select(func.count(User.id))
            .where(User.role == "EMPLOYEE")
            .where(User.is_active == True)
        ).scalar() or 0
        
        # 5. Avis en attente de modération (status=PENDING)
        pending_reviews = db.execute(
            select(func.count(Review.id))
            .where(Review.status == "PENDING")
        ).scalar() or 0
        
        # 6. Messages de contact non traités (status=SENT)
        pending_messages = db.execute(
            select(func.count(ContactMessage.id))
            .where(ContactMessage.status == "SENT")
        ).scalar() or 0
        
        return {
            "total_orders_today": total_orders_today,
            "total_revenue_today": total_revenue_today,
            "total_revenue_all_time": total_revenue_all_time,
            "pending_orders": pending_orders,
            "active_employees": active_employees,
            "pending_reviews": pending_reviews,
            "pending_messages": pending_messages
        }
    
    except Exception as e:
        # Log détaillé de l'erreur
        logger.error(f"❌ Erreur dans get_dashboard_kpi: {e}", exc_info=True)
        # Retourner des valeurs par défaut au lieu de crasher
        return {
            "total_orders_today": 0,
            "total_revenue_today": 0.0,
            "total_revenue_all_time": 0.0,
            "pending_orders": 0,
            "active_employees": 0,
            "pending_reviews": 0,
            "pending_messages": 0
        }
