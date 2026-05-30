from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import get_db
from app.models import EventDB
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)):
    health_status = "OK"
    db_status = "connected"
    stores_health = {}
    
    # 1. Check Database connection
    try:
        # Simple query to check connection
        db.execute(text("SELECT 1")).scalar()
    except Exception as e:
        health_status = "DEGRADED"
        db_status = "disconnected"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "UNHEALTHY",
            "database": db_status,
            "error": f"Database unavailable: {str(e)}",
            "stores": {}
        }

    # 2. Query last event timestamp per store
    try:
        # Get list of unique store IDs
        store_ids_res = db.query(EventDB.store_id).distinct().all()
        store_ids = [r[0] for r in store_ids_res]

        now = datetime.utcnow()

        for store_id in store_ids:
            last_ts = db.query(func.max(EventDB.timestamp)).filter(EventDB.store_id == store_id).scalar()
            if last_ts:
                # Calculate lag in minutes
                lag_seconds = (now - last_ts).total_seconds()
                lag_minutes = round(lag_seconds / 60.0, 1)
                
                # Flag as STALE_FEED if lag > 10 minutes
                feed_status = "ACTIVE"
                if lag_minutes > 10:
                    feed_status = "STALE_FEED"
                    health_status = "DEGRADED"

                stores_health[store_id] = {
                    "last_event_timestamp": last_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "lag_minutes": lag_minutes,
                    "status": feed_status
                }
    except Exception as e:
        health_status = "DEGRADED"
        stores_health = {"error": f"Failed to retrieve store status: {str(e)}"}

    return {
        "status": health_status,
        "database": db_status,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stores": stores_health
    }
