# Apex Lens — Store Intelligence

**Apex Lens** turns store CCTV into clear numbers: how many real shoppers came in, where they went, and how many actually bought. Built for offline beauty retail (Purplle-style stores).

---

## The problem (in simple words)

Most stores already have **CCTV cameras** and a **billing system (POS)**. But they don’t talk to each other.

### What goes wrong today

1. **You can’t see the full shopper journey**  
   One camera sees the door. Another sees the aisles. Another sees the billing counter. Nobody connects them into one story: *entered → browsed → queued → paid*.

2. **Staff look like customers**  
   Employees walk the floor all day. If you count every person on camera, your “footfall” is too high and your **conversion rate looks worse than it really is**.

3. **Video doesn’t become KPIs by itself**  
   Watching five camera feeds doesn’t give you dwell time, queue length, dead zones, or a funnel chart. Someone has to **detect people, track them, and log events**.

4. **Demos often break**  
   Many student or hackathon projects show a pretty UI with **empty charts** because the database wasn’t seeded, SQLite locked up, or the API wasn’t running. Reviewers can’t judge what you built.

5. **Hard to run for others**  
   “Install Python, create venv, seed DB, run three terminals…” is fine for you, not for a judge who only has five minutes.

### What stores actually need

One honest number as the **north star**:

**Conversion rate = shoppers who paid ÷ real visitors (staff not counted)**

Plus: zone heatmaps, queue alerts, and live CCTV when you need to verify what the numbers mean.

---

## How our solution fixes this

We built a full path from **camera video → events → API → dashboard**.

```
CCTV → detect people (YOLO) → track them (ByteTrack) → tag staff & zones → save events → charts
```

| Problem | What we do |
|--------|------------|
| Cameras don’t connect | Same visitor gets events across entry, floor, and billing cameras. |
| Staff inflate numbers | Black-coat detection sets `is_staff`; APIs ignore staff in funnel and KPIs. |
| Video ≠ metrics | Pipeline emits `ENTRY`, `ZONE_ENTER`, `BILLING_QUEUE_JOIN`, etc. Dashboard reads live APIs. |
| Empty / broken demos | DB auto-creates and **seeds sample data** on startup. Docker starts everything with one command. |
| Hard to reproduce | `docker compose up --build` → API on **8000**, **Apex Lens** UI on **3000**. |

### What makes Apex Lens different

- **Apex Lens UI** — gold + plum “retail command” look, conversion ring, journey rail, staff-aware callout (not a generic purple admin template).
- **Two dashboards** — React for executives; legacy page on port 8000 for face detection and staff/customer boxes on video.
- **Real pipeline** — YOLO on your 5 MP4s, simulator for edge cases, pytest, `DESIGN.md` / `CHOICES.md`.

More detail: [DESIGN.md](DESIGN.md) · [CHOICES.md](CHOICES.md)

---

## Quick start (Docker — one command)

**You need:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) running.

```bash
cd store-intelligence
docker compose up --build
```

| What you get | URL |
|--------------|-----|
| **Apex Lens dashboard** | http://localhost:3000 |
| **API docs** | http://localhost:8000/docs |
| **CV lab (faces + staff on video)** | http://localhost:8000/ |

No `.env` file. No manual seed. Database and sample analytics are created inside the container.

Add `-d` to run in the background.

---

## Quick start (local, no Docker)

**Terminal 1 — API**
```powershell
cd store-intelligence
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Apex Lens UI**
```powershell
cd store-intelligence\dashboard-ui
npm install
npm run dev
```

Open http://localhost:3000 (API must be on port 8000).

---

## API (short list)

| Endpoint | What it does |
|----------|----------------|
| `POST /events/ingest` | Add camera events (safe to send duplicates) |
| `GET /stores/{id}/metrics` | Visitors, conversion, dwell, queue |
| `GET /stores/{id}/funnel` | Entry → browse → billing → purchase |
| `GET /stores/{id}/heatmap` | Busiest zones |
| `GET /stores/{id}/anomalies` | Queue spikes, dead zones |
| `GET /health` | Is the DB up? Are cameras stale? |

---

## Project layout

```text
store-intelligence/
├── app/              FastAPI + SQLite
├── pipeline/         YOLO, tracking, staff, zones, simulator
├── dashboard-ui/     Apex Lens (React)
├── dashboard/        Legacy HTML + CCTV videos
├── data/             Layout, POS sample, DB (local)
├── tests/            pytest
└── docker-compose.yml
```

---

## Tests

```powershell
pytest tests/ -v
```

---

## Optional: more data

```powershell
# Simulated shoppers (groups, re-entry, queues, staff)
python -m pipeline.emit_simulated --mode batch

# YOLO on 5 MP4s in dashboard/assets/cctv/
python scripts/run_yolo_five_cameras.py --frame-stride 8
```
