import argparse
import sys
import os
import time
import uuid
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Ensure we can import from pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.emit import emit_event_batch

API_URL = os.getenv("API_URL", "http://localhost:8000")

def generate_simulated_data(base_date: datetime) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    # Formulate timestamps relative to base_date (e.g. today at 14:00:00)
    # Return (events, transactions)
    
    events = []
    transactions = []
    store_id = "STORE_BLR_002"

    def dt_str(minutes_offset: float) -> str:
        t = base_date + timedelta(minutes=minutes_offset)
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Helper to generate uuid
    def make_id():
        return str(uuid.uuid4())

    # --- 1. Staff Member (Staff Exclusion) ---
    # Staff enters early and stays in store, moving through zones
    staff_id = "VIS_staff01"
    events.extend([
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": staff_id, "event_type": "ENTRY", "timestamp": dt_str(0), "zone_id": None, "dwell_ms": 0, "is_staff": True, "confidence": 0.99, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": staff_id, "event_type": "ZONE_ENTER", "timestamp": dt_str(1), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": True, "confidence": 0.98, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": staff_id, "event_type": "ZONE_DWELL", "timestamp": dt_str(5), "zone_id": "SKINCARE", "dwell_ms": 240000, "is_staff": True, "confidence": 0.98, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": staff_id, "event_type": "ZONE_EXIT", "timestamp": dt_str(10), "zone_id": "SKINCARE", "dwell_ms": 540000, "is_staff": True, "confidence": 0.98, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 4}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": staff_id, "event_type": "ZONE_ENTER", "timestamp": dt_str(11), "zone_id": "HAIRCARE", "dwell_ms": 0, "is_staff": True, "confidence": 0.99, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 5}},
    ])

    # --- 2. Customer A (Normal Conversion) ---
    cust_a = "VIS_custA01"
    events.extend([
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_a, "event_type": "ENTRY", "timestamp": dt_str(2), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_a, "event_type": "ZONE_ENTER", "timestamp": dt_str(3), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_a, "event_type": "ZONE_DWELL", "timestamp": dt_str(3.5), "zone_id": "SKINCARE", "dwell_ms": 30000, "is_staff": False, "confidence": 0.94, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_a, "event_type": "ZONE_EXIT", "timestamp": dt_str(4.5), "zone_id": "SKINCARE", "dwell_ms": 90000, "is_staff": False, "confidence": 0.94, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 4}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_a, "event_type": "ZONE_ENTER", "timestamp": dt_str(5), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.96, "metadata": {"session_seq": 5}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_a, "event_type": "BILLING_QUEUE_JOIN", "timestamp": dt_str(5.1), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.96, "metadata": {"queue_depth": 1, "session_seq": 6}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_a, "event_type": "ZONE_EXIT", "timestamp": dt_str(7.5), "zone_id": "BILLING", "dwell_ms": 150000, "is_staff": False, "confidence": 0.96, "metadata": {"session_seq": 7}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_a, "event_type": "EXIT", "timestamp": dt_str(8), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 8}}
    ])
    # POS Transaction within 5 mins of billing entry (billing entry is 5.0, transaction is at 7.0)
    transactions.append({
        "store_id": store_id,
        "transaction_id": "TXN_SIM_001",
        "timestamp": dt_str(7.0),
        "basket_value_inr": 1250.00
    })

    # --- 3. Customer B & C (Group Entry) ---
    # They enter at the same time
    cust_b = "VIS_custB02"
    cust_c = "VIS_custC02"
    events.extend([
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_b, "event_type": "ENTRY", "timestamp": dt_str(10), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.93, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_c, "event_type": "ENTRY", "timestamp": dt_str(10), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 1}},
        
        # Walk together to Haircare
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_b, "event_type": "ZONE_ENTER", "timestamp": dt_str(11), "zone_id": "HAIRCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_c, "event_type": "ZONE_ENTER", "timestamp": dt_str(11), "zone_id": "HAIRCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.91, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 2}},
        
        # B leaves without purchase (Abandonment)
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_b, "event_type": "ZONE_EXIT", "timestamp": dt_str(13), "zone_id": "HAIRCARE", "dwell_ms": 120000, "is_staff": False, "confidence": 0.93, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_b, "event_type": "EXIT", "timestamp": dt_str(13.5), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.93, "metadata": {"session_seq": 4}},

        # C goes to billing
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_c, "event_type": "ZONE_EXIT", "timestamp": dt_str(14), "zone_id": "HAIRCARE", "dwell_ms": 180000, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_c, "event_type": "ZONE_ENTER", "timestamp": dt_str(14.5), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 4}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_c, "event_type": "BILLING_QUEUE_JOIN", "timestamp": dt_str(14.6), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"queue_depth": 1, "session_seq": 5}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_c, "event_type": "ZONE_EXIT", "timestamp": dt_str(17.5), "zone_id": "BILLING", "dwell_ms": 180000, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 6}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_c, "event_type": "EXIT", "timestamp": dt_str(18), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 7}}
    ])
    # POS Transaction for Customer C (billing entry 14.5, transaction 16.0)
    transactions.append({
        "store_id": store_id,
        "transaction_id": "TXN_SIM_002",
        "timestamp": dt_str(16.0),
        "basket_value_inr": 680.00
    })

    # --- 4. Customer D (Re-entry Handling) ---
    cust_d = "VIS_custD03"
    events.extend([
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_d, "event_type": "ENTRY", "timestamp": dt_str(20), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.96, "metadata": {"session_seq": 1}},
        # Exits briefly to answer call
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_d, "event_type": "EXIT", "timestamp": dt_str(21), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.96, "metadata": {"session_seq": 2}},
        # Re-enters (REENTRY)
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_d, "event_type": "REENTRY", "timestamp": dt_str(21.5), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 3}},
        
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_d, "event_type": "ZONE_ENTER", "timestamp": dt_str(22), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 4}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_d, "event_type": "ZONE_EXIT", "timestamp": dt_str(23.5), "zone_id": "SKINCARE", "dwell_ms": 90000, "is_staff": False, "confidence": 0.94, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 5}},
        
        # Billing queue join
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_d, "event_type": "ZONE_ENTER", "timestamp": dt_str(24), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 6}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_d, "event_type": "BILLING_QUEUE_JOIN", "timestamp": dt_str(24.1), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.95, "metadata": {"queue_depth": 1, "session_seq": 7}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_d, "event_type": "ZONE_EXIT", "timestamp": dt_str(26), "zone_id": "BILLING", "dwell_ms": 120000, "is_staff": False, "confidence": 0.95, "metadata": {"session_seq": 8}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_d, "event_type": "EXIT", "timestamp": dt_str(26.5), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.96, "metadata": {"session_seq": 9}}
    ])
    # POS Transaction (billing entry 24.0, transaction 25.5)
    transactions.append({
        "store_id": store_id,
        "transaction_id": "TXN_SIM_003",
        "timestamp": dt_str(25.5),
        "basket_value_inr": 2100.00
    })

    # --- 5. Customer E (Queue Buildup & Abandonment) ---
    cust_e = "VIS_custE04"
    events.extend([
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_e, "event_type": "ENTRY", "timestamp": dt_str(22), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_e, "event_type": "ZONE_ENTER", "timestamp": dt_str(22.5), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_e, "event_type": "ZONE_EXIT", "timestamp": dt_str(24.2), "zone_id": "SKINCARE", "dwell_ms": 102000, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 3}},
        
        # Enters billing zone while Customer D is there -> Queue depth spikes to 2
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_e, "event_type": "ZONE_ENTER", "timestamp": dt_str(24.5), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.93, "metadata": {"session_seq": 4}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_e, "event_type": "BILLING_QUEUE_JOIN", "timestamp": dt_str(24.6), "zone_id": "BILLING", "dwell_ms": 0, "is_staff": False, "confidence": 0.93, "metadata": {"queue_depth": 2, "session_seq": 5}},
        
        # Abandons billing queue because it is too long (no transaction follows!)
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_BILL_02", "visitor_id": cust_e, "event_type": "ZONE_EXIT", "timestamp": dt_str(25.8), "zone_id": "BILLING", "dwell_ms": 78000, "is_staff": False, "confidence": 0.93, "metadata": {"session_seq": 6}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_e, "event_type": "EXIT", "timestamp": dt_str(26.2), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 7}}
    ])

    # --- 6. Customer F (Partial Occlusion / Low Confidence Calibration) ---
    cust_f = "VIS_custF05"
    events.extend([
        # Low confidence ENTRY due to occlusion near display rack
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_f, "event_type": "ENTRY", "timestamp": dt_str(27), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.45, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_f, "event_type": "ZONE_ENTER", "timestamp": dt_str(27.5), "zone_id": "HAIRCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.52, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_f, "event_type": "ZONE_EXIT", "timestamp": dt_str(29), "zone_id": "HAIRCARE", "dwell_ms": 90000, "is_staff": False, "confidence": 0.55, "metadata": {"sku_zone": "SHAMPOO", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_f, "event_type": "EXIT", "timestamp": dt_str(29.5), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.48, "metadata": {"session_seq": 4}}
    ])

    # --- 7. Empty Store Period ---
    # No visitor events generated between dt_str(30) and dt_str(40).
    # Tests that zero traffic does not crash API queries.

    # --- 8. Overlapping Fields of View ---
    cust_g = "VIS_custG06"
    events.extend([
        # Tracked in Entry Camera and Main Camera simultaneously
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_g, "event_type": "ENTRY", "timestamp": dt_str(41), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 1}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_g, "event_type": "ZONE_ENTER", "timestamp": dt_str(41.1), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_MAIN_02", "visitor_id": cust_g, "event_type": "ZONE_EXIT", "timestamp": dt_str(42.5), "zone_id": "SKINCARE", "dwell_ms": 84000, "is_staff": False, "confidence": 0.92, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 3}},
        {"event_id": make_id(), "store_id": store_id, "camera_id": "CAM_ENTRY_02", "visitor_id": cust_g, "event_type": "EXIT", "timestamp": dt_str(43), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.94, "metadata": {"session_seq": 4}}
    ])

    # --- 9. Extra data for Heatmap rendering ---
    # Let's add multiple brief entries across other stores so heatmap endpoints return populated data
    stores = ["STORE_BLR_001", "STORE_DEL_001", "STORE_MUM_001", "STORE_MUM_002"]
    for s_idx, s_id in enumerate(stores):
        v_id = f"VIS_ext_{s_id[:5]}_{s_idx}"
        events.extend([
            {"event_id": make_id(), "store_id": s_id, "camera_id": f"CAM_ENTRY_{s_idx+1}", "visitor_id": v_id, "event_type": "ENTRY", "timestamp": dt_str(1), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.9, "metadata": {"session_seq": 1}},
            {"event_id": make_id(), "store_id": s_id, "camera_id": f"CAM_MAIN_{s_idx+1}", "visitor_id": v_id, "event_type": "ZONE_ENTER", "timestamp": dt_str(2), "zone_id": "SKINCARE", "dwell_ms": 0, "is_staff": False, "confidence": 0.88, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 2}},
            {"event_id": make_id(), "store_id": s_id, "camera_id": f"CAM_MAIN_{s_idx+1}", "visitor_id": v_id, "event_type": "ZONE_EXIT", "timestamp": dt_str(5), "zone_id": "SKINCARE", "dwell_ms": 180000, "is_staff": False, "confidence": 0.88, "metadata": {"sku_zone": "MOISTURISER", "session_seq": 3}},
            {"event_id": make_id(), "store_id": s_id, "camera_id": f"CAM_ENTRY_{s_idx+1}", "visitor_id": v_id, "event_type": "EXIT", "timestamp": dt_str(6), "zone_id": None, "dwell_ms": 0, "is_staff": False, "confidence": 0.9, "metadata": {"session_seq": 4}}
        ])
        transactions.append({
            "store_id": s_id,
            "transaction_id": f"TXN_EXT_{s_idx}",
            "timestamp": dt_str(4),
            "basket_value_inr": 1500.00
        })

    # Sort events by timestamp so they flow in order
    events.sort(key=lambda x: x["timestamp"])
    
    return events, transactions

def seed_pos_transactions_to_db(transactions: List[Dict[str, Any]]):
    # Inserts transactions directly into SQLite db
    # We load transactions directly into the CSV or DB
    import sqlite3
    db_path = os.getenv("DATABASE_PATH")
    if not db_path:
        db_url = os.getenv("DATABASE_URL")
        if db_url and db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
        else:
            db_path = "d:/APEX RETAIL_KASH/store-intelligence/data/store_intelligence.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure transactions table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        store_id TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        basket_value_inr REAL NOT NULL
    )
    """)
    
    for txn in transactions:
        # Parse timestamp to sqlite format
        ts = txn["timestamp"].replace("Z", "").replace("T", " ")
        cursor.execute(
            "INSERT OR REPLACE INTO transactions (transaction_id, store_id, timestamp, basket_value_inr) VALUES (?, ?, ?, ?)",
            (txn["transaction_id"], txn["store_id"], ts, txn["basket_value_inr"])
        )
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(transactions)} transactions directly into SQLite DB.")

def ingest_events_batch(events: List[Dict[str, Any]]):
    print(f"Ingesting {len(events)} events in batch mode...")
    # Send in chunks of 100
    chunk_size = 100
    for i in range(0, len(events), chunk_size):
        chunk = events[i:i+chunk_size]
        res = emit_event_batch(chunk)
        print(f"Ingested batch {i//chunk_size + 1}: status {res['status_code']}, response: {res['response']}")

def stream_events_realtime(events: List[Dict[str, Any]]):
    print(f"Streaming {len(events)} events in simulated real time...")
    # Map the relative timestamps to now
    start_time = datetime.utcnow()
    
    # We find relative offsets of each event from the first event
    first_event_time = datetime.fromisoformat(events[0]["timestamp"].replace("Z", "+00:00"))
    
    for event in events:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        offset_seconds = (event_time - first_event_time).total_seconds()
        
        # Adjust timestamp to current wall clock time
        target_time = start_time + timedelta(seconds=offset_seconds)
        event["timestamp"] = target_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Wait until target time
        now = datetime.utcnow()
        wait_seconds = (target_time - now).total_seconds()
        if wait_seconds > 0:
            # Scale wait time to speed up simulation (1s real = 10s simulation)
            scale = 0.1 
            time.sleep(wait_seconds * scale)
            
        # Emit single event in list
        emit_event_batch([event])
        print(f"Emitted: {event['event_type']} for {event['visitor_id']} at {event['timestamp']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate retail CCTV events and feed them to the API.")
    parser.add_argument("--mode", choices=["batch", "stream"], default="batch", help="Batch seed or real-time stream.")
    args = parser.parse_args()

    # Establish base date. We use current time minus 30 minutes to seed a realistic past timeline.
    base_date = datetime.utcnow() - timedelta(minutes=45)
    
    events, transactions = generate_simulated_data(base_date)
    
    # First seed POS transactions directly to database
    # Since POS transactions are from POS registers and not the camera feeds,
    # they are stored directly in the database.
    seed_pos_transactions_to_db(transactions)
    
    if args.mode == "batch":
        ingest_events_batch(events)
    else:
        stream_events_realtime(events)
