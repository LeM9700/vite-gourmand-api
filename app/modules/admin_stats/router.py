from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db_postgres import get_db
from app.core.db_mongo import get_mongo_db
from app.modules.auth.deps import require_admin
from app.modules.admin_stats.service import recompute_menu_daily_stats

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])

@router.post("/recompute")
def recompute(day: date = Query(...), db: Session = Depends(get_db), _admin = Depends(require_admin)):
    mongo_db = get_mongo_db()
    return recompute_menu_daily_stats(db=db, mongo_db=mongo_db, day=day)

@router.get("/menus/daily")
def get_daily(day: date = Query(...), _admin = Depends(require_admin)):
    mongo_db = get_mongo_db()
    docs = list(mongo_db["menu_stats_daily"].find({"day": day.isoformat()}, {"_id": 0}))
    return {"day": day.isoformat(), "items": docs}
