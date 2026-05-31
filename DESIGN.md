# DESIGN.md — Purplle / Apex Store Intelligence Architecture

**North star metric:** Offline Store Conversion Rate = Customers who purchased ÷ Total unique visitors (staff excluded).

---

## 1. System overview

Raw CCTV → structured events → REST API → live dashboard.

```
CCTV Video → YOLOv8 detect → ByteTrack → Staff/Zone classify → Events → API → Dashboard
```

| Stage | Module | Role |
|-------|--------|------|
| 1 | `pipeline/detect.py` | Person detection (YOLOv8n, conf ≥ 0.35) |
| 2 | `pipeline/byte_tracker.py` | Multi-object tracking (two-stage IoU match) |
| 3 | `pipeline/staff_detector.py` | Black coat / uniform HSV on torso ROI |
| 4 | `pipeline/zone_classifier.py` | Polygon or heuristic zone mapping |
| 5 | `pipeline/tracker.py` | Session events (ENTRY, dwell, queue, REENTRY) |
| 6 | `pipeline/emit.py` | JSONL + batch POST `/events/ingest` |
| 7 | `app/*` | Metrics, funnel, heatmap, anomalies, health |
| 8 | `dashboard/index.html` | Live CCTV + analytics UI |

**Fallback:** `pipeline/emit_simulated.py` seeds all edge-case scenarios when GPU/OpenCV unavailable.

---

## 2. Event model

| Field | Purpose |
|-------|---------|
| `event_id` | UUID v4 — idempotent ingest |
| `visitor_id` | Stable session token (`VIS_*`) |
| `event_type` | ENTRY, EXIT, REENTRY, ZONE_*, BILLING_QUEUE_JOIN |
| `dwell_ms` | Integer milliseconds (not float seconds) |
| `is_staff` | Excluded from conversion funnel & KPIs |
| `metadata.session_seq` | Reconstruct visitor timeline |

---

## 3. Edge case handling

| Edge case | Strategy |
|-----------|----------|
| **Group entry (2–4 people)** | Separate ByteTrack ID per bbox — no merging |
| **Staff movement** | HSV uniform on torso; `is_staff=True`; filtered in API queries |
| **Re-entry (exit + return)** | 5-min window + 150px spatial Re-ID; `REENTRY` event |
| **Partial occlusion** | ByteTrack stage-2 low-conf (0.1–0.35) recovery |
| **Empty store** | No events → API returns zeros, not 500 |
| **Billing queue** | `BILLING_QUEUE_JOIN` + `queue_depth`; anomaly on spike |
| **Camera overlap** | Same `visitor_id` via Re-ID registry across cameras |

Simulation coverage: `emit_simulated.py` explicitly models staff, groups, re-entry, queue abandonment, occlusion, empty periods, and cross-camera overlap.

---

## 4. Key metrics

- **Conversion:** Billing zone visit + POS txn within 5 minutes
- **Funnel:** Entry → Zone Visit → Billing Queue → Purchase (drop-off %)
- **Heatmap:** Unique visitors per zone + normalized dwell score (0–100)
- **Anomalies:** Queue spike, dead zone, conversion drop
- **Health:** DB status, per-store feed lag, stale camera alerts

---

## 5. Production notes

- **Idempotency:** `event_id` primary key; duplicate ingest skipped
- **Graceful degradation:** DB lock → 503 structured JSON; CV missing → simulation
- **Scale bottleneck:** At ~40 live stores, SQLite write throughput — upgrade via `DATABASE_URL=postgresql://...`
- **Run pipeline:** `bash pipeline/run.sh clips ./clips` or `bash pipeline/run.sh simulate`

---

## 6. Dashboard

Single-page app at `http://localhost:8000/` — 5-camera CCTV, face/staff detection overlay, funnel chart, zone heatmap, floor map. Polls API every 5s; dashboard also pushes CCTV footfall to `/events/ingest` for live analytics.
