# CHOICES.md — Architectural Decisions (Purplle Challenge)

Three decisions that shaped the system, with what AI suggested vs what we chose.

---

## Decision 1: YOLOv8-nano + ByteTrack (not DeepSORT)

| Option | Pros | Cons |
|--------|------|------|
| YOLOv8n + ByteTrack | ~15fps CPU, two-stage low-conf recovery | Lower mAP on tiny distant faces |
| YOLOv8-medium + DeepSORT | Better accuracy | OSNet per frame → ~4fps CPU |
| Browser face-api only | No server GPU | Not a real CCTV pipeline |

**AI suggested:** YOLOv8-small + DeepSORT, confidence threshold 0.5.

**We chose:** YOLOv8-nano + ByteTrack at **0.35** high / **0.1** low threshold.

**Why:** Challenge requires graceful degradation on low confidence — dropping at 0.5 loses partially occluded shoppers in billing queues. ByteTrack stage-2 recovers them without OSNet latency. For retail counting, **recall > precision** (missed visitor inflates conversion).

**What broke first:** YOLO `box.id` without `model.track()` — fixed by separate `byte_tracker.py` module.

---

## Decision 2: Event schema — `dwell_ms` integer + `session_seq`

**AI suggested:** `dwell_seconds: float` and per-frame confidence arrays.

**We chose:** `dwell_ms: int` and single `confidence` per event + `metadata.session_seq`.

**Why:** Integer ms avoids float drift when summing dwell across sessions. `session_seq` lets funnel dedupe without scanning full visitor history — AI did not propose this; we added it for funnel performance.

**Staff attire:** `metadata.attire = black_coat` optional field; primary signal is `is_staff` boolean.

---

## Decision 3: Staff detection — HSV uniform (not custom classifier)

| Approach | Verdict |
|----------|---------|
| Train binary classifier | No labelled data at challenge time |
| VLM per crop | ~87% accuracy but API cost + latency |
| **HSV torso ROI** | CPU-only, black coat / navy / purple profiles |

**Purplle context:** Beauty retail staff wear distinctive solid uniforms (black coat in our CCTV dataset). Dashboard uses **RGB luminance** on live video; pipeline uses **OpenCV HSV** on YOLO bboxes — same heuristic, two runtimes.

**False positive risk:** Customer in dark jacket → may tag as staff. Mitigation: temporal smoothing (12-frame history) on dashboard; pipeline sets confidence from coverage score.

---

## Decision 4: SQLite now, PostgreSQL upgrade path

**AI suggested:** PostgreSQL from day one.

**We chose:** SQLite with WAL + `DATABASE_URL` swap for PostgreSQL.

**Why:** `docker compose up` must work on reviewer laptop with zero infra. Challenge scope (~15k events) fits SQLite. At 40 stores × 3 cameras live, **writes break first** — documented in DESIGN.md; fix is connection pool + Postgres partition by `store_id` + day.

---

## Decision 5: Dashboard — vanilla HTML vs React

**We chose:** FastAPI-served SPA (`dashboard/index.html`) + Chart.js.

**Why:** One port (`8000`), no npm build, works with local MP4 CCTV files. React would score bonus points but adds compose complexity; our dashboard includes live 5-camera video, face-api, staff badges, and real ingest — not a mock.

---

## AI usage (transparent)

- Used for scaffolding FastAPI routes and dashboard layout
- **Overrode** DeepSORT recommendation after profiling CPU latency
- **Overrode** float dwell_seconds after reasoning about billing edge cases
- **Added** CCTV→API ingest bridge and black-coat staff logic based on actual Purplle store footage behavior

See git history: commits document incremental changes (CCTV feeds, SQLite lock fix, staff classification).
