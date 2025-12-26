from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, cast, Date as SqlDate

from app.modules.orders.models import Order
from app.modules.reviews.models import Review

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
