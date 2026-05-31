"""API endpoint tests — happy path + edge cases."""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import EventDB

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_events():
    """Clear events between tests for isolated metrics."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(EventDB).delete()
        db.commit()
    finally:
        db.close()
    yield


def _event(**kwargs):
    base = {
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_BLR_002",
        "camera_id": "CAM_ENTRY_02",
        "visitor_id": "VIS_test_01",
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zone_id": None,
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {"session_seq": 1},
    }
    base.update(kwargs)
    return base


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "database" in body


def test_ingest_and_deduplicate():
    ev = _event()
    r1 = client.post("/events/ingest", json=[ev])
    assert r1.status_code in (200, 201, 207)
    r2 = client.post("/events/ingest", json=[ev])
    data = r2.json()
    assert data.get("skipped", 0) >= 1 or data.get("ingested", 0) == 0


def test_ingest_staff_excluded_from_funnel():
    """Staff events ingested but funnel counts customers only."""
    batch = [
        _event(visitor_id="VIS_cust_a", event_type="ENTRY"),
        _event(
            visitor_id="VIS_cust_a",
            camera_id="CAM_MAIN_02",
            event_type="ZONE_ENTER",
            zone_id="SKINCARE",
            metadata={"session_seq": 2, "sku_zone": "MOISTURISER"},
        ),
        _event(visitor_id="VIS_staff_x", event_type="ENTRY", is_staff=True),
    ]
    client.post("/events/ingest", json=batch)
    funnel = client.get("/stores/STORE_BLR_002/funnel").json()
    assert funnel["funnel"][0]["count"] == 1


def test_empty_store_metrics():
    r = client.get("/stores/STORE_BLR_002/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["unique_visitors"] == 0
    assert data["conversion_rate"] == 0.0


def test_funnel_after_customer_journey():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    batch = [
        _event(visitor_id="VIS_j1", event_type="ENTRY", timestamp=ts),
        _event(
            visitor_id="VIS_j1",
            camera_id="CAM_MAIN_02",
            event_type="ZONE_ENTER",
            zone_id="SKINCARE",
            timestamp=ts,
            metadata={"session_seq": 2},
        ),
        _event(
            visitor_id="VIS_j1",
            camera_id="CAM_BILL_02",
            event_type="BILLING_QUEUE_JOIN",
            zone_id="BILLING",
            timestamp=ts,
            metadata={"session_seq": 3, "queue_depth": 1},
        ),
    ]
    client.post("/events/ingest", json=batch)
    funnel = client.get("/stores/STORE_BLR_002/funnel").json()
    assert funnel["funnel"][0]["count"] >= 1
    assert funnel["funnel"][2]["count"] >= 1


def test_heatmap_zones():
    client.post("/events/ingest", json=[
        _event(
            visitor_id="VIS_h1",
            camera_id="CAM_MAIN_02",
            event_type="ZONE_ENTER",
            zone_id="SKINCARE",
            metadata={"session_seq": 1},
        ),
    ])
    hm = client.get("/stores/STORE_BLR_002/heatmap").json()
    assert "zones" in hm


def test_ingest_batch_limit():
    big = [_event(event_id=str(uuid.uuid4())) for _ in range(501)]
    r = client.post("/events/ingest", json=big)
    assert r.status_code == 400
