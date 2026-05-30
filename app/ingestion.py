from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db, db_write_lock
from app.models import EventSchema, EventDB
from datetime import datetime
import json

router = APIRouter()

@router.post("/events/ingest")
def ingest_events(payload: List[Dict[str, Any]], response: Response, db: Session = Depends(get_db)):
    # Check limit of 500 events
    if len(payload) > 500:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "status": "failed",
            "message": "Batch size exceeds limit of 500 events",
            "ingested": 0,
            "skipped": 0,
            "errors": [{"index": -1, "error": "Batch size exceeds limit of 500"}]
        }

    errors = []
    events_to_insert = []
    skipped_count = 0
    ingested_count = 0

    # Read all existing event_ids in the batch to avoid querying the DB one-by-one (bulk checking)
    event_ids_in_payload = []
    for item in payload:
        if isinstance(item, dict) and "event_id" in item:
            event_ids_in_payload.append(str(item["event_id"]))
            
    existing_ids = set()
    if event_ids_in_payload:
        query_res = db.query(EventDB.event_id).filter(EventDB.event_id.in_(event_ids_in_payload)).all()
        existing_ids = {r[0] for r in query_res}

    for idx, raw_event in enumerate(payload):
        # 1. Pydantic validation
        try:
            event = EventSchema(**raw_event)
        except Exception as e:
            errors.append({
                "index": idx,
                "event_id": raw_event.get("event_id") if isinstance(raw_event, dict) else None,
                "error": str(e)
            })
            continue

        # 2. Check duplicates (idempotency)
        if event.event_id in existing_ids:
            skipped_count += 1
            continue

        # 3. Prepare DB object
        try:
            # Parse timestamp to timezone-aware datetime
            ts_str = event.timestamp
            if ts_str.endswith("Z"):
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                ts = datetime.fromisoformat(ts_str)

            # Extract flattened metadata fields
            q_depth = None
            s_zone = None
            s_seq = 1
            if event.metadata:
                q_depth = event.metadata.queue_depth
                s_zone = event.metadata.sku_zone
                s_seq = event.metadata.session_seq or 1

            db_event = EventDB(
                event_id=event.event_id,
                store_id=event.store_id,
                camera_id=event.camera_id,
                visitor_id=event.visitor_id,
                event_type=event.event_type,
                timestamp=ts,
                zone_id=event.zone_id,
                dwell_ms=event.dwell_ms,
                is_staff=event.is_staff,
                confidence=event.confidence,
                queue_depth=q_depth,
                sku_zone=s_zone,
                session_seq=s_seq
            )
            events_to_insert.append(db_event)
            # Add to local set to avoid duplicates within the same batch
            existing_ids.add(event.event_id)
        except Exception as e:
            errors.append({
                "index": idx,
                "event_id": event.event_id,
                "error": f"Internal mapping error: {str(e)}"
            })

    # Bulk insert (serialized with simulator/seed writes)
    if events_to_insert:
        try:
            with db_write_lock:
                db.bulk_save_objects(events_to_insert)
                db.commit()
            ingested_count = len(events_to_insert)
        except Exception as e:
            db.rollback()
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {
                "status": "failed",
                "message": "Database insert failed",
                "ingested": 0,
                "skipped": 0,
                "errors": [{"index": -1, "error": str(e)}]
            }

    # Set response code
    if errors:
        if ingested_count == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            status_str = "failed"
        else:
            response.status_code = status.HTTP_207_MULTI_STATUS
            status_str = "partial_success"
    else:
        response.status_code = status.HTTP_201_CREATED
        status_str = "success"

    return {
        "status": status_str,
        "ingested": ingested_count,
        "skipped": skipped_count,
        "errors": errors
    }
