# Apex Retail Store Intelligence System

Apex Retail Store Intelligence is a containerized real-time computer vision analytics system designed to process CCTV footage and POS sales transactions, exposing store-level efficiency insights through a REST API and a premium web-based executive dashboard.

---

## 1. Directory Structure

```text
store-intelligence/
├── app/                      # FastAPI Backend Service
│   ├── __init__.py           # Package namespace initializer
│   ├── anomalies.py          # GET /stores/{id}/anomalies route
│   ├── database.py           # SQLAlchemy SQLite database session setup
│   ├── funnel.py             # GET /stores/{id}/funnel analysis
│   ├── health.py             # GET /health node & feed staleness check
│   ├── heatmap.py            # GET /stores/{id}/heatmap zone occupancy
│   ├── main.py               # FastAPI core app & structured logging
│   ├── metrics.py            # GET /stores/{id}/metrics store KPIs
│   └── models.py             # Pydantic schemas & SQLAlchemy DB models
│
├── pipeline/                 # Computer Vision & Simulation Pipeline
│   ├── __init__.py           # Package namespace initializer
│   ├── detect.py             # YOLOv8 object detector
│   ├── emit.py               # Event poster client
│   ├── emit_simulated.py     # Complex customer behavior simulator
│   ├── tracker.py            # Re-ID, cross-camera, and dwell tracker
│   └── run.sh                # Executable pipeline wrapper
│
├── data/                     # Data Storage
│   ├── pos_transactions.csv  # Base POS transactions CSV
│   ├── store_layout.json     # Configuration defining store layouts & camera placements
│   └── store_intelligence.db # Initialized SQLite database
│
├── dashboard/                # Live Dashboard
│   └── index.html            # Premium single-page glassmorphism dashboard UI
│
├── Dockerfile                # Deployment container blueprint
├── docker-compose.yml        # Orchestration configuration
├── requirements.txt          # Python packages list
├── DESIGN.md                 # Architecture, tracker, and algorithm design spec
└── CHOICES.md                # Stack decisions and technology trade-offs
```

---

## 2. Quick Start: Docker Compose (API + React Dashboard)

Runs **API on port 8000** and **React dashboard on port 3000**:

```bash
docker compose up --build -d
```

| Service | URL |
|---------|-----|
| **React dashboard** | http://localhost:3000 |
| **API + Swagger** | http://localhost:8000/docs |
| **Legacy HTML dashboard** (CCTV overlays, face-api) | http://localhost:8000/ |

**Seed analytics (simulation — all edge cases):**
```bash
docker exec -it store_intelligence_api python -m pipeline.emit_simulated --mode batch
```

**YOLO on 5 local MP4s (full CV pipeline):**
```bash
# Host (with venv + ultralytics):
python scripts/run_yolo_five_cameras.py --frame-stride 4

# Or Docker pipeline profile (GPU/CPU heavy):
docker compose --profile pipeline up pipeline
```

**React dev (without Docker):**
```bash
cd dashboard-ui && npm install && npm run dev
# API must run on :8000 — Vite proxies /api → :8000
```

---

## 3. Local Installation & Development Setup

If you prefer to run the application locally without Docker, follow these steps:

### Prerequisite
- **Python 3.8 to 3.11** installed.

### Step 1: Clone and Set Up Virtual Environment
On Windows (PowerShell):
```powershell
# Navigate to the workspace
cd "d:\APEX RETAIL_KASH\store-intelligence"

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run the FastAPI Server
Start Uvicorn in development auto-reload mode:
```powershell
uvicorn app.main:app --reload --port 8000
```
- The backend API is now running at `http://localhost:8000`.
- The live dashboard is served directly at the root: `http://localhost:8000/`.
- Interactive API Swagger docs are hosted at `http://localhost:8000/docs`.

### Step 4: Run the Ingestion Pipeline Simulator
Open a new terminal window (with active virtual env) and execute the ingestion script to feed tracking events:
```powershell
# Run the pipeline in batch mode to seed historical events
python -m pipeline.emit_simulated --mode batch

# OR run in real-time stream mode (emits events in real-time wall-clock speed)
python -m pipeline.emit_simulated --mode stream
```

---

## 4. API Endpoints Map

### Ingestion API
- `POST /events/ingest` – Ingests a bulk batch of camera event objects. Fully supports duplicate detection and idempotency.

### Analytics APIs
- `GET /stores/{store_id}/metrics` – High-level KPIs: unique visitors, conversion rate, average dwell time, queue depth, queue abandonment rate.
- `GET /stores/{store_id}/funnel` – 4-stage customer conversion funnel counts and drop-off percentages.
- `GET /stores/{store_id}/heatmap` – Store-wide zone visit frequencies and absolute dwell scores.
- `GET /stores/{store_id}/anomalies` – Identifies real-time bottlenecks (queue depth spikes, dead zones, conversion drops).

### System Health
- `GET /health` – Verifies SQLite connectivity and flags stale camera feeds if lag exceeds 10 minutes.

---

## 5. Structured Logging & Error Handling

- **Structured Logging**: Every API request writes a single JSON log to stdout containing trace IDs, latency, response status, and endpoints, matching production logging standards.
- **Error Handling**: Graceful database failover via global SQLAlchemy handlers. Returns structured JSON errors (`DATABASE_UNAVAILABLE`) if connection to SQLite is broken.
