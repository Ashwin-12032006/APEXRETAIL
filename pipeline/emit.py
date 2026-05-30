import os
import requests
import json
from typing import List, Dict, Any

API_URL = os.getenv("API_URL", "http://localhost:8000")

def emit_event_batch(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    url = f"{API_URL}/events/ingest"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=events, headers=headers, timeout=10)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code != 500 else {"error": "Internal Server Error"}
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 503,
            "response": {"error": f"Failed to connect to API: {str(e)}"}
        }
