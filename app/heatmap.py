from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EventDB
from app.metrics import get_store_time_window
from typing import Dict, List, Any

router = APIRouter()

@router.get("/stores/{store_id}/heatmap")
def get_store_heatmap(store_id: str, db: Session = Depends(get_db)):
    start_time, end_time = get_store_time_window(db, store_id)
    if not start_time:
        return {
            "store_id": store_id,
            "data_confidence": False,
            "zones": []
        }

    # Fetch events
    events = db.query(EventDB).filter(
        EventDB.store_id == store_id,
        EventDB.timestamp >= start_time,
        EventDB.timestamp <= end_time,
        EventDB.is_staff == False
    ).all()

    # Total sessions in window
    total_sessions = len(set(ev.visitor_id for ev in events))
    data_confidence = total_sessions >= 20

    # Calculate zone frequency (unique visitor_ids visiting the zone) and average dwell time
    # Group by zone_id
    zone_visitors: Dict[str, set] = {}
    zone_dwells: Dict[str, list] = {}

    for ev in events:
        if not ev.zone_id or ev.zone_id == "ENTRY_EXIT":
            continue
        
        if ev.zone_id not in zone_visitors:
            zone_visitors[ev.zone_id] = set()
        zone_visitors[ev.zone_id].add(ev.visitor_id)

        if ev.dwell_ms > 0:
            if ev.zone_id not in zone_dwells:
                zone_dwells[ev.zone_id] = []
            zone_dwells[ev.zone_id].append(ev.dwell_ms)

    # Compute raw values
    raw_zones = []
    max_freq = 0
    max_dwell = 0.0

    # Get union of all zones
    all_zones = set(zone_visitors.keys()).union(set(zone_dwells.keys()))

    for zone in all_zones:
        freq = len(zone_visitors.get(zone, set()))
        dwells = zone_dwells.get(zone, [])
        avg_dwell = sum(dwells) / len(dwells) if dwells else 0.0

        if freq > max_freq:
            max_freq = freq
        if avg_dwell > max_dwell:
            max_dwell = avg_dwell

        raw_zones.append({
            "zone_id": zone,
            "visit_frequency": freq,
            "avg_dwell_ms": int(avg_dwell)
        })

    # Normalise scores (0 to 100)
    zones_heatmap = []
    for zone_data in raw_zones:
        freq_score = 0.0
        if max_freq > 0:
            freq_score = round((zone_data["visit_frequency"] / max_freq) * 100, 1)

        dwell_score = 0.0
        if max_dwell > 0:
            dwell_score = round((zone_data["avg_dwell_ms"] / max_dwell) * 100, 1)

        zones_heatmap.append({
            "zone_id": zone_data["zone_id"],
            "visit_frequency": zone_data["visit_frequency"],
            "visit_frequency_score": freq_score,
            "avg_dwell_ms": zone_data["avg_dwell_ms"],
            "avg_dwell_score": dwell_score
        })

    return {
        "store_id": store_id,
        "data_confidence": data_confidence,
        "zones": zones_heatmap
    }
