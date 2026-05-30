"""One-shot seed for funnel / heatmap (run while API is stopped if DB was locked)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.seed_data import ensure_analytics_data

if __name__ == "__main__":
    ensure_analytics_data("STORE_BLR_002", min_events=80)
    print("Done. Restart uvicorn and refresh the dashboard.")
