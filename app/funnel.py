from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EventDB, TransactionDB
from app.metrics import get_store_time_window
from typing import Dict, List, Any

router = APIRouter()


def _naive_dt(dt):
    """SQLite may return naive or aware datetimes; normalize for subtraction."""
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None:
        return dt.replace(tzinfo=None)
    return dt

@router.get("/stores/{store_id}/funnel")
def get_store_funnel(store_id: str, db: Session = Depends(get_db)):
    start_time, end_time = get_store_time_window(db, store_id)
    if not start_time:
        return {
            "store_id": store_id,
            "funnel": [
                {"stage": "Entry", "count": 0, "drop_off_pct": 0.0},
                {"stage": "Zone Visit", "count": 0, "drop_off_pct": 0.0},
                {"stage": "Billing Queue", "count": 0, "drop_off_pct": 0.0},
                {"stage": "Purchase", "count": 0, "drop_off_pct": 0.0}
            ]
        }

    # Fetch events and transactions
    events = db.query(EventDB).filter(
        EventDB.store_id == store_id,
        EventDB.timestamp >= start_time,
        EventDB.timestamp <= end_time,
        EventDB.is_staff == False
    ).all()

    transactions = db.query(TransactionDB).filter(
        TransactionDB.store_id == store_id,
        TransactionDB.timestamp >= start_time,
        TransactionDB.timestamp <= end_time
    ).all()

    # Group by visitor_id
    sessions: Dict[str, list] = {}
    for ev in events:
        if ev.visitor_id not in sessions:
            sessions[ev.visitor_id] = []
        sessions[ev.visitor_id].append(ev)

    total_entries = len(sessions)
    zone_visits = 0
    billing_queue = 0
    purchases = 0

    for visitor_id, ev_list in sessions.items():
        # 1. Zone Visit check (visited at least one named product zone besides ENTRY_EXIT/BILLING)
        has_zone_visit = any(
            ev.zone_id not in [None, "ENTRY_EXIT", "BILLING"]
            for ev in ev_list
        )
        if has_zone_visit:
            zone_visits += 1

        # 2. Billing Queue check (visited BILLING zone)
        has_billing = any(
            ev.zone_id == "BILLING" or ev.event_type == "BILLING_QUEUE_JOIN"
            for ev in ev_list
        )
        if has_billing:
            billing_queue += 1

            # 3. Purchase check (billing entry + 5 minute POS txn correlation)
            billing_evs = [ev for ev in ev_list if ev.zone_id == "BILLING" or ev.event_type == "BILLING_QUEUE_JOIN"]
            billing_entry = _naive_dt(min(ev.timestamp for ev in billing_evs))
            
            for txn in transactions:
                time_diff = (_naive_dt(txn.timestamp) - billing_entry).total_seconds()
                if 0 <= time_diff <= 300: # 5 minutes
                    purchases += 1
                    break

    # Calculate drop-off percentages
    # Drop-off % = (Previous Count - Current Count) / Previous Count * 100%
    drop_off_zone = 0.0
    if total_entries > 0:
        drop_off_zone = round(((total_entries - zone_visits) / total_entries) * 100, 2)

    drop_off_billing = 0.0
    if zone_visits > 0:
        drop_off_billing = round(((zone_visits - billing_queue) / zone_visits) * 100, 2)
    elif total_entries > 0:
        drop_off_billing = 100.0

    drop_off_purchase = 0.0
    if billing_queue > 0:
        drop_off_purchase = round(((billing_queue - purchases) / billing_queue) * 100, 2)
    elif zone_visits > 0 or total_entries > 0:
        drop_off_purchase = 100.0

    return {
        "store_id": store_id,
        "funnel": [
            {"stage": "Entry", "count": total_entries, "drop_off_pct": 0.0},
            {"stage": "Zone Visit", "count": zone_visits, "drop_off_pct": drop_off_zone},
            {"stage": "Billing Queue", "count": billing_queue, "drop_off_pct": drop_off_billing},
            {"stage": "Purchase", "count": purchases, "drop_off_pct": drop_off_purchase}
        ]
    }
