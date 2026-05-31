"""
Event schema definition and emission to JSONL + Intelligence API.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("emit")

API_URL = os.getenv("API_URL", "http://localhost:8000")


class EventType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ZONE_ENTER = "ZONE_ENTER"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_DWELL = "ZONE_DWELL"
    BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
    BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"
    REENTRY = "REENTRY"


class EventEmitter:
    """Writes validated events to JSONL and batches to /events/ingest."""

    def __init__(
        self,
        store_id: str,
        camera_id: str,
        output_path: Path,
        api_url: Optional[str] = None,
        batch_size: int = 50,
    ):
        self.store_id = store_id
        self.camera_id = camera_id
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_url = api_url or API_URL
        self.batch_size = batch_size
        self._buffer: List[dict] = []
        self._file = open(self.output_path, "a", encoding="utf-8")
        logger.info("EventEmitter → %s", self.output_path)

    def emit(
        self,
        event_type: EventType,
        visitor_id: str,
        zone_id: Optional[str],
        timestamp: datetime,
        confidence: float,
        is_staff: bool,
        session_seq: int,
        dwell_ms: int = 0,
        queue_depth: Optional[int] = None,
        sku_zone: Optional[str] = None,
    ) -> dict:
        event = {
            "event_id": str(uuid.uuid4()),
            "store_id": self.store_id,
            "camera_id": self.camera_id,
            "visitor_id": visitor_id,
            "event_type": event_type.value if isinstance(event_type, EventType) else event_type,
            "timestamp": timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "zone_id": zone_id,
            "dwell_ms": dwell_ms,
            "is_staff": is_staff,
            "confidence": round(float(confidence), 4),
            "metadata": {
                "queue_depth": queue_depth,
                "sku_zone": sku_zone or zone_id,
                "session_seq": session_seq,
            },
        }
        self._file.write(json.dumps(event) + "\n")
        self._buffer.append(event)
        if len(self._buffer) >= self.batch_size:
            self._flush_to_api()
        return event

    def _flush_to_api(self):
        if not self.api_url or not self._buffer:
            return
        try:
            resp = requests.post(
                f"{self.api_url.rstrip('/')}/events/ingest",
                json=self._buffer,
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Flushed %d events to API", len(self._buffer))
        except Exception as e:
            logger.warning("API flush failed: %s — events remain in JSONL", e)
        self._buffer = []

    def flush(self):
        self._flush_to_api()
        self._file.flush()
        self._file.close()


def emit_event_batch(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy helper — POST list of events to ingest endpoint."""
    url = f"{API_URL.rstrip('/')}/events/ingest"
    try:
        response = requests.post(url, json=events, headers={"Content-Type": "application/json"}, timeout=10)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else {},
        }
    except requests.exceptions.RequestException as e:
        return {"status_code": 503, "response": {"error": str(e)}}
