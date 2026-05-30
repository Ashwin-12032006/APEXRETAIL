"""
Seed SQLite with analytics-friendly events so funnel / heatmap / KPIs populate.
Runs once at startup when event count is low (before live simulator).
"""
import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy import func
from app.database import SessionLocal, db_write_lock
from app.models import EventDB, TransactionDB


CAMERA_ZONE_MAP = {
    "CAM1": ("CAM_ENTRY_02", None, ["ENTRY", "EXIT"]),
    "CAM2": ("CAM_MAIN_02", "SKINCARE", ["ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT"]),
    "CAM3": ("CAM_BILL_02", "BILLING", ["ZONE_ENTER", "BILLING_QUEUE_JOIN", "ZONE_EXIT"]),
    "CAM4": ("CAM_MAIN_02", "HAIRCARE", ["ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT"]),
    "CAM5": ("CAM_BILL_02", "BILLING", ["ZONE_ENTER", "BILLING_QUEUE_JOIN"]),
}


def _parse_ts(ts_str: str) -> datetime:
    if ts_str.endswith("Z"):
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.fromisoformat(ts_str)


def _events_from_simulated_payload(events: list) -> list:
    rows = []
    for raw in events:
        meta = raw.get("metadata") or {}
        ts = _parse_ts(raw["timestamp"])
        rows.append(
            EventDB(
                event_id=raw["event_id"],
                store_id=raw["store_id"],
                camera_id=raw["camera_id"],
                visitor_id=raw["visitor_id"],
                event_type=raw["event_type"],
                timestamp=ts,
                zone_id=raw.get("zone_id"),
                dwell_ms=raw.get("dwell_ms") or 0,
                is_staff=raw.get("is_staff", False),
                confidence=raw["confidence"],
                queue_depth=meta.get("queue_depth"),
                sku_zone=meta.get("sku_zone"),
                session_seq=meta.get("session_seq", 1),
            )
        )
    return rows


def _generate_five_camera_traffic(store_id: str, base: datetime) -> tuple:
    """Recent footfall tied to each of the 5 CCTV angles (maps to your MP4 feeds)."""
    events = []
    transactions = []
    visitors_per_cam = 6

    for cam_key, (camera_id, zone_id, event_types) in CAMERA_ZONE_MAP.items():
        for i in range(visitors_per_cam):
            vid = f"VIS_{cam_key}_{i:02d}"
            offset_min = random.uniform(-90, -5)
            seq = 1
            for et in event_types:
                t = base + timedelta(minutes=offset_min + seq * 0.4)
                events.append(
                    {
                        "event_id": str(uuid.uuid4()),
                        "store_id": store_id,
                        "camera_id": camera_id,
                        "visitor_id": vid,
                        "event_type": et,
                        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "zone_id": zone_id,
                        "dwell_ms": random.randint(15000, 120000) if "DWELL" in et else 0,
                        "is_staff": False,
                        "confidence": round(random.uniform(0.88, 0.98), 2),
                        "metadata": {
                            "session_seq": seq,
                            "sku_zone": random.choice(["MOISTURISER", "SHAMPOO", None]),
                            "queue_depth": random.randint(1, 4) if "QUEUE" in et else None,
                        },
                    }
                )
                seq += 1
            if zone_id == "BILLING" and random.random() > 0.35:
                bill_t = base + timedelta(minutes=offset_min + 2)
                transactions.append(
                    TransactionDB(
                        transaction_id=f"TXN_{cam_key}_{i}_{uuid.uuid4().hex[:6]}",
                        store_id=store_id,
                        timestamp=bill_t,
                        basket_value_inr=round(random.uniform(400, 2800), 2),
                    )
                )

    return events, transactions


def ensure_analytics_data(store_id: str = "STORE_BLR_002", min_events: int = 80) -> None:
    """Insert seed events if the store DB is sparse (powers funnel + heatmap widgets)."""
    with db_write_lock:
        db = SessionLocal()
        try:
            count = (
                db.query(func.count(EventDB.event_id))
                .filter(EventDB.store_id == store_id)
                .scalar()
                or 0
            )
            if count >= min_events:
                return

            from pipeline.emit_simulated import generate_simulated_data

            now = datetime.utcnow()
            base = now - timedelta(minutes=45)
            sim_events, sim_txns = generate_simulated_data(base)
            cam_events, cam_txns = _generate_five_camera_traffic(store_id, now - timedelta(minutes=30))

            all_event_rows = _events_from_simulated_payload(sim_events + cam_events)
            db.bulk_save_objects(all_event_rows)

            for txn in sim_txns:
                db.add(
                    TransactionDB(
                        transaction_id=txn["transaction_id"],
                        store_id=txn["store_id"],
                        timestamp=_parse_ts(txn["timestamp"]),
                        basket_value_inr=txn["basket_value_inr"],
                    )
                )
            for txn in cam_txns:
                db.add(txn)

            db.commit()
            print(
                f"[Seed] Loaded {len(all_event_rows)} events + "
                f"{len(sim_txns) + len(cam_txns)} transactions for {store_id}"
            )
        except Exception as e:
            db.rollback()
            print(f"[Seed] Analytics seed failed: {e}")
        finally:
            db.close()
