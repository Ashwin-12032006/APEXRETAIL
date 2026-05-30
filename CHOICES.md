# CHOICES.md - Tech Stack & Architecture Trade-offs

This document details the engineering trade-offs and rationale behind key architectural decisions made for the **Apex Retail Store Intelligence** system.

---

## 1. Web Framework: FastAPI (Python)
### Selection: **FastAPI**
- **Pros**:
  - **High Performance**: Built on top of Starlette and Pydantic, making it one of the fastest Python frameworks (comparable to Go and Node.js).
  - **Auto Documentation**: Out-of-the-box Swagger UI (`/docs`) speeds up endpoint testing and integration.
  - **Asynchronous natively**: Excellent for handling multiple high-frequency CCTV event stream connection pings.
- **Alternatives Considered**: 
  - *Flask*: Highly customizable but requires manual integration of Pydantic validation, OpenAPI specs, and lacks native async capabilities.
  - *Django*: Overkill for a microservice; brings heavy ORM boilerplate that is slower to spin up and containerize.

---

## 2. Storage Engine: SQLite
### Selection: **SQLite (via SQLAlchemy)**
- **Pros**:
  - **Zero Configuration**: No external service dependencies or complex container networks needed. Highly portable.
  - **Speed**: Operates directly in-memory or as a single local file, delivering extremely fast read-write speeds for prototyping.
  - **Thread-safe**: Configured with `check_same_thread: False` to support FastAPI's multi-threaded requests safely.
- **Alternatives Considered**:
  - *PostgreSQL*: Superior for production scaling and complex spatial indexing, but introduces network setup dependencies that complicate local hiring challenge evaluation. SQLite was selected to guarantee a **one-command out-of-the-box build**.

---

## 3. Tracking & Computer Vision: YOLOv8 with Simulation Fallback
### Selection: **Ultralytics YOLOv8 Nano (`yolov8n`) + Fallback Simulation**
- **Pros**:
  - **State-of-the-Art Speed**: Nano weights run efficiently on standard CPUs without requiring expensive CUDA-compatible GPUs.
  - **Graceful Fallback**: If the evaluation environment lacks torch or OpenCV, the system seamlessly uses `pipeline/emit_simulated.py` to seed structured business scenarios.
- **Alternatives Considered**:
  - *ByteTrack / DeepOCSORT*: Advanced tracking filters that add heavy mathematical dependencies. Proximity-based IoU matching was implemented in `tracker.py` to keep the codebase simple, clean, and easily understandable.

---

## 4. Re-ID Strategy: Proximity & Intertemporal Correlation
### Selection: **Proximity + Co-occurrence Matching Window**
- **Pros**:
  - Highly efficient; operates in $\mathcal{O}(1)$ or minor list-scanning iterations.
  - Excludes staff tracking, handles short exit/re-entries (60s matching window), and correlates coordinates between overlapping entrance feeds.
- **Alternatives Considered**:
  - *Neural Feature Embeddings (Re-ID)*: Running a deep feature extractor (e.g. ResNet50) on every cropped bounding box computes heavy vector distances. It is accurate across occlusions but reduces throughput from 30 FPS to <5 FPS on standard CPUs.

---

## 5. Live Dashboard Stack: Standalone HTML5 + Glassmorphism CSS + Chart.js
### Selection: **Vanilla Single-Page App (SPA) served via FastAPI**
- **Pros**:
  - **Ultra-lightweight**: Eliminates npm build steps, Webpack compilation, and transpilers.
  - **Portability**: Accessible directly at the backend root `http://localhost:8000/` or as a standalone double-clickable local file.
  - **Aesthetics**: Glassmorphism transparent cards, Outfit font, and linear gradients deliver a high-end SaaS feel that immediately stands out.
- **Alternatives Considered**:
  - *React / Next.js*: Excellent for large-scale enterprise suites, but adds thousands of node modules, heavy build sizes, and complicates single-command execution within Docker.
