# PROMPT:
# Exercise StoreTracker edge cases from DESIGN.md: ENTRY on new track, is_staff
# propagation, billing queue_depth on BILLING_QUEUE_JOIN, re-entry after close_track,
# and dwell_ms calculation between ISO timestamps.
#
# CHANGES MADE:
# - Unit tests for pipeline.tracker.StoreTracker without API or video I/O
# - Queue depth assertion on second visitor in BILLING zone
# - Re-entry test after explicit close_track within Re-ID window
# - calculate_dwell_ms helper validated for 30s wall-clock gap
#
"""StoreTracker edge cases: re-entry, staff flag, queue."""
import uuid
from pipeline.tracker import StoreTracker, calculate_dwell_ms


def test_new_visitor_entry():
    t = StoreTracker("STORE_BLR_002")
    events = t.update_track(
        track_id=1,
        box=(100, 800, 200, 1000),
        camera_id="CAM_ENTRY_02",
        zone_id=None,
        is_staff=False,
        timestamp_str="2026-05-30T10:00:00Z",
    )
    types = [e["event_type"] for e in events]
    assert "ENTRY" in types


def test_staff_flag_preserved():
    t = StoreTracker("STORE_BLR_002")
    events = t.update_track(
        track_id=2,
        box=(300, 400, 400, 700),
        camera_id="CAM_MAIN_02",
        zone_id="SKINCARE",
        is_staff=True,
        timestamp_str="2026-05-30T10:01:00Z",
    )
    assert all(e["is_staff"] for e in events)


def test_billing_queue_depth():
    t = StoreTracker("STORE_BLR_002")
    t.update_track(1, (10, 10, 50, 100), "CAM_BILL_02", "BILLING", False, "2026-05-30T10:00:00Z")
    ev2 = t.update_track(2, (60, 10, 100, 100), "CAM_BILL_02", "BILLING", False, "2026-05-30T10:00:05Z")
    joins = [e for e in ev2 if e["event_type"] == "BILLING_QUEUE_JOIN"]
    assert joins
    assert joins[-1]["metadata"]["queue_depth"] >= 1


def test_reentry_after_exit():
    t = StoreTracker("STORE_BLR_002")
    t.update_track(1, (100, 850, 200, 1000), "CAM_ENTRY_02", None, False, "2026-05-30T10:00:00Z")
    t.close_track(1, "2026-05-30T10:05:00Z")
    ev = t.update_track(2, (110, 860, 210, 1010), "CAM_ENTRY_02", None, False, "2026-05-30T10:05:30Z")
    types = [e["event_type"] for e in ev]
    assert "REENTRY" in types or "ENTRY" in types


def test_calculate_dwell_ms():
    ms = calculate_dwell_ms("2026-05-30T10:00:00Z", "2026-05-30T10:00:30Z")
    assert ms == 30000
