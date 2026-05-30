import time
import uuid
import json
import sys
import os
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, Base
from app.ingestion import router as ingestion_router
from app.metrics import router as metrics_router
from app.funnel import router as funnel_router
from app.heatmap import router as heatmap_router
from app.anomalies import router as anomalies_router
from app.health import router as health_router

# Create DB Tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database table initialization failed: {e}", file=sys.stderr)

# Start real-time store simulator background thread
try:
    from app.live_simulator import start_live_simulator
    start_live_simulator()
except Exception as e:
    print(f"Live simulator start failed: {e}", file=sys.stderr)

app = FastAPI(
    title="Apex Retail Store Intelligence API",
    description="Real-time CCTV-based store tracking and POS transaction analytics API.",
    version="1.0.0"
)

# Mount static assets directory
dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")
assets_dir = os.path.join(dashboard_dir, "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for database connection issues (Part C: Graceful Degradation)
@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Log the detailed database error internally
    print(f"Database error occurred: {exc}", file=sys.stderr)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "type": "DATABASE_UNAVAILABLE",
            "message": "The database is temporarily unavailable. Please try again later."
        }
    )

# Structured Logging Middleware (Part C: Structured Logging)
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Try to extract event count for ingest endpoint
    event_count = None
    if request.url.path == "/events/ingest" and request.method == "POST":
        # Cache body to read it and allow it to be read again
        body = await request.body()
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive
        try:
            payload = json.loads(body)
            if isinstance(payload, list):
                event_count = len(payload)
        except Exception:
            pass

    response = await call_next(request)
    
    # Compute latency
    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    
    # Extract store_id from path if available
    store_id = None
    path_parts = request.url.path.split('/')
    if "stores" in path_parts:
        try:
            idx = path_parts.index("stores")
            if idx + 1 < len(path_parts):
                store_id = path_parts[idx + 1]
        except ValueError:
            pass

    # Build structured log dictionary
    log_record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "store_id": store_id,
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
        "event_count": event_count
    }
    
    # Write structured log to stdout
    print(json.dumps(log_record))
    
    # Propagate trace ID in response headers
    response.headers["X-Trace-ID"] = trace_id
    return response

# Include APIRouters
app.include_router(ingestion_router, tags=["Ingestion"])
app.include_router(metrics_router, tags=["Analytics"])
app.include_router(funnel_router, tags=["Analytics"])
app.include_router(heatmap_router, tags=["Analytics"])
app.include_router(anomalies_router, tags=["Analytics"])
app.include_router(health_router, tags=["Health"])

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Load dashboard/index.html and serve it directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(os.path.dirname(current_dir), "dashboard", "index.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Store Intelligence Dashboard HTML Not Found</h1>")
