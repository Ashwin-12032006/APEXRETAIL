from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import EventDB, TransactionDB
from datetime import datetime, timedelta
from typing import Dict, Any

router = APIRouter()

def get_store_time_window(db: Session, store_id: str):
    # Find the latest event timestamp in the database to establish "now"
    max_event_ts = db.query(func.max(EventDB.timestamp)).filter(EventDB.store_id == store_id).scalar()
    if not max_event_ts:
        return None, None
    
    # We define our 24-hour window ending at the latest event timestamp
    end_time = max_event_ts
    start_time = end_time - timedelta(hours=24)
    return start_time, end_time

@router.get("/stores/{store_id}/metrics")
def get_store_metrics(store_id: str, db: Session = Depends(get_db)):
    start_time, end_time = get_store_time_window(db, store_id)
    if not start_time:
        # Return default metrics for empty store
        return {
            "store_id": store_id,
            "unique_visitors": 0,
            "conversion_rate": 0.0,
            "avg_dwell_by_zone": {},
            "queue_depth": 0,
            "abandonment_rate": 0.0
        }

    # Fetch all events (excluding staff) for this store in the window
    events = db.query(EventDB).filter(
        EventDB.store_id == store_id,
        EventDB.timestamp >= start_time,
        EventDB.timestamp <= end_time,
        EventDB.is_staff == False
    ).order_by(EventDB.timestamp).all()

    # Fetch all transactions for this store in the window
    transactions = db.query(TransactionDB).filter(
        TransactionDB.store_id == store_id,
        TransactionDB.timestamp >= start_time,
        TransactionDB.timestamp <= end_time
    ).all()

    # Group events by visitor_id (sessions)
    sessions: Dict[str, list] = {}
    for ev in events:
        if ev.visitor_id not in sessions:
            sessions[ev.visitor_id] = []
        sessions[ev.visitor_id].append(ev)

    # 1. Unique visitors count
    unique_visitors = len(sessions)

    # 2. Conversion rate calculation
    # A visitor session is converted if:
    # They visited the Billing zone, and a POS transaction occurred in that store
    # within the window: [billing_entry_time, billing_entry_time + 5 minutes]
    converted_sessions = set()
    billing_visitors = set()

    for visitor_id, ev_list in sessions.items():
        # Find billing entry time
        billing_evs = [ev for ev in ev_list if ev.zone_id == "BILLING" or ev.event_type == "BILLING_QUEUE_JOIN"]
        if billing_evs:
            billing_entry = min(ev.timestamp for ev in billing_evs)
            billing_visitors.add(visitor_id)
            
            # Check if there is any POS transaction within 5 minutes after billing entry
            for txn in transactions:
                # Time difference in seconds
                time_diff = (txn.timestamp - billing_entry).total_seconds()
                if 0 <= time_diff <= 300: # 5 minutes
                    converted_sessions.add(visitor_id)
                    break

    conversion_rate = 0.0
    if unique_visitors > 0:
        conversion_rate = round(len(converted_sessions) / unique_visitors, 4)

    # 3. Avg dwell per zone
    # Calculate sum and count of dwell_ms per zone_id
    zone_dwells: Dict[str, list] = {}
    for ev in events:
        if ev.zone_id and ev.dwell_ms > 0:
            if ev.zone_id not in zone_dwells:
                zone_dwells[ev.zone_id] = []
            zone_dwells[ev.zone_id].append(ev.dwell_ms)

    avg_dwell_by_zone = {}
    for zone, dwells in zone_dwells.items():
        avg_dwell_by_zone[zone] = int(sum(dwells) / len(dwells))

    # 4. Queue depth (latest queue depth event in billing zone)
    # Find latest event in billing zone reporting queue_depth
    queue_depth = 0
    billing_queue_events = [ev for ev in events if ev.zone_id == "BILLING" and ev.queue_depth is not None]
    if billing_queue_events:
        # Sort by timestamp
        billing_queue_events.sort(key=lambda x: x.timestamp)
        queue_depth = billing_queue_events[-1].queue_depth or 0

    # 5. Abandonment rate
    # Visitors who entered billing but did NOT convert / Total visitors who entered billing
    abandoned_count = len(billing_visitors) - len(converted_sessions)
    abandonment_rate = 0.0
    if len(billing_visitors) > 0:
        abandonment_rate = round(abandoned_count / len(billing_visitors), 4)

    return {
        "store_id": store_id,
        "unique_visitors": unique_visitors,
        "conversion_rate": conversion_rate,
        "avg_dwell_by_zone": avg_dwell_by_zone,
        "queue_depth": queue_depth,
        "abandonment_rate": abandonment_rate
    }
