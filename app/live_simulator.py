import time
import random
import uuid
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.database import SessionLocal, db_write_lock
from app.models import EventDB, TransactionDB

# Active customer tracking state
# Format: {visitor_id: {state: 'entered'|'skincare'|'haircare'|'billing', entry_time: datetime, zone_entry_time: datetime, dwell_ms: int, session_seq: int}}
active_shoppers = {}
state_lock = threading.Lock()


def safe_commit(db: Session) -> None:
    with db_write_lock:
        db.commit()


def simulate_realtime_traffic():
    """Background loop that continuously inserts realistic tracking events and POS transactions."""
    print("Background Live Store Simulator Started.")
    
    # Store ID to simulate
    store_id = "STORE_BLR_002"
    
    while True:
        db: Session = None
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            with state_lock:
                # Clean up old active shoppers that got stuck (older than 30 mins)
                stuck_ids = [vid for vid, info in active_shoppers.items() if (now - info['entry_time']).total_seconds() > 1800]
                for vid in stuck_ids:
                    active_shoppers.pop(vid)
                
                # Decision matrix: what action to take?
                action = random.choice(['entry', 'move_zone', 'dwell_zone', 'checkout_join', 'checkout_complete', 'staff_action'])
                
                # If no shoppers in store, force an entry
                if not active_shoppers:
                    action = 'entry'
                
                if action == 'entry':
                    # Generate a new customer
                    visitor_id = f"VIS_cust_{str(uuid.uuid4())[:8]}"
                    active_shoppers[visitor_id] = {
                        'state': 'entered',
                        'entry_time': now,
                        'zone_entry_time': None,
                        'dwell_ms': 0,
                        'session_seq': 1
                    }
                    
                    event = EventDB(
                        event_id=str(uuid.uuid4()),
                        store_id=store_id,
                        camera_id="CAM_ENTRY_02",
                        visitor_id=visitor_id,
                        event_type="ENTRY",
                        timestamp=now,
                        zone_id=None,
                        dwell_ms=0,
                        is_staff=False,
                        confidence=round(random.uniform(0.92, 0.98), 2),
                        queue_depth=None,
                        sku_zone=None,
                        session_seq=1
                    )
                    db.add(event)
                    safe_commit(db)
                    # print(f"[Sim] Customer entered: {visitor_id}")
                    
                elif action == 'move_zone':
                    # Find a customer who is just 'entered' and move them to Skincare or Haircare
                    candidates = [vid for vid, info in active_shoppers.items() if info['state'] == 'entered']
                    if candidates:
                        visitor_id = random.choice(candidates)
                        zone = random.choice(['SKINCARE', 'HAIRCARE'])
                        info = active_shoppers[visitor_id]
                        info['state'] = zone.lower()
                        info['zone_entry_time'] = now
                        info['session_seq'] += 1
                        
                        event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_MAIN_02",
                            visitor_id=visitor_id,
                            event_type="ZONE_ENTER",
                            timestamp=now,
                            zone_id=zone,
                            dwell_ms=0,
                            is_staff=False,
                            confidence=round(random.uniform(0.90, 0.96), 2),
                            queue_depth=None,
                            sku_zone="MOISTURISER" if zone == "SKINCARE" else "SHAMPOO",
                            session_seq=info['session_seq']
                        )
                        db.add(event)
                        safe_commit(db)
                        # print(f"[Sim] Customer {visitor_id} entered zone {zone}")
                        
                elif action == 'dwell_zone':
                    # Find a customer in skincare or haircare and increase their dwell
                    candidates = [vid for vid, info in active_shoppers.items() if info['state'] in ['skincare', 'haircare']]
                    if candidates:
                        visitor_id = random.choice(candidates)
                        info = active_shoppers[visitor_id]
                        zone = info['state'].upper()
                        
                        # Add random dwell time (10-30 seconds)
                        added_dwell = random.randint(10000, 30000)
                        info['dwell_ms'] += added_dwell
                        info['session_seq'] += 1
                        
                        event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_MAIN_02",
                            visitor_id=visitor_id,
                            event_type="ZONE_DWELL",
                            timestamp=now,
                            zone_id=zone,
                            dwell_ms=info['dwell_ms'],
                            is_staff=False,
                            confidence=round(random.uniform(0.90, 0.97), 2),
                            queue_depth=None,
                            sku_zone="MOISTURISER" if zone == "SKINCARE" else "SHAMPOO",
                            session_seq=info['session_seq']
                        )
                        db.add(event)
                        safe_commit(db)
                        # print(f"[Sim] Customer {visitor_id} dwelled in {zone} for {info['dwell_ms']}ms")
                        
                elif action == 'checkout_join':
                    # Move a skincare/haircare customer to the billing queue
                    candidates = [vid for vid, info in active_shoppers.items() if info['state'] in ['skincare', 'haircare']]
                    if candidates:
                        visitor_id = random.choice(candidates)
                        info = active_shoppers[visitor_id]
                        old_zone = info['state'].upper()
                        
                        # Exit old zone
                        info['session_seq'] += 1
                        exit_event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_MAIN_02",
                            visitor_id=visitor_id,
                            event_type="ZONE_EXIT",
                            timestamp=now,
                            zone_id=old_zone,
                            dwell_ms=info['dwell_ms'],
                            is_staff=False,
                            confidence=round(random.uniform(0.90, 0.97), 2),
                            queue_depth=None,
                            sku_zone="MOISTURISER" if old_zone == "SKINCARE" else "SHAMPOO",
                            session_seq=info['session_seq']
                        )
                        db.add(exit_event)
                        
                        # Enter billing zone and join queue
                        info['state'] = 'billing'
                        info['zone_entry_time'] = now
                        info['dwell_ms'] = 0
                        info['session_seq'] += 1
                        
                        # Count current queue depth in billing state
                        queue_depth = sum(1 for vid, sh in active_shoppers.items() if sh['state'] == 'billing')
                        
                        enter_event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_BILL_02",
                            visitor_id=visitor_id,
                            event_type="ZONE_ENTER",
                            timestamp=now,
                            zone_id="BILLING",
                            dwell_ms=0,
                            is_staff=False,
                            confidence=round(random.uniform(0.93, 0.98), 2),
                            queue_depth=None,
                            sku_zone=None,
                            session_seq=info['session_seq']
                        )
                        db.add(enter_event)
                        
                        info['session_seq'] += 1
                        join_event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_BILL_02",
                            visitor_id=visitor_id,
                            event_type="BILLING_QUEUE_JOIN",
                            timestamp=now,
                            zone_id="BILLING",
                            dwell_ms=0,
                            is_staff=False,
                            confidence=round(random.uniform(0.93, 0.98), 2),
                            queue_depth=queue_depth,
                            sku_zone=None,
                            session_seq=info['session_seq']
                        )
                        db.add(join_event)
                        safe_commit(db)
                        # print(f"[Sim] Customer {visitor_id} joined billing queue (depth {queue_depth})")
                        
                elif action == 'checkout_complete':
                    # Make a billing customer pay and exit
                    candidates = [vid for vid, info in active_shoppers.items() if info['state'] == 'billing']
                    if candidates:
                        visitor_id = random.choice(candidates)
                        info = active_shoppers[visitor_id]
                        
                        # 80% convert to purchase, 20% abandon queue (tests abandonment metrics!)
                        will_purchase = random.random() < 0.8
                        
                        info['session_seq'] += 1
                        dwell_time = int((now - info['zone_entry_time']).total_seconds() * 1000)
                        
                        # Exit billing zone
                        exit_event = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_BILL_02",
                            visitor_id=visitor_id,
                            event_type="ZONE_EXIT",
                            timestamp=now,
                            zone_id="BILLING",
                            dwell_ms=dwell_time,
                            is_staff=False,
                            confidence=round(random.uniform(0.93, 0.98), 2),
                            queue_depth=None,
                            sku_zone=None,
                            session_seq=info['session_seq']
                        )
                        db.add(exit_event)
                        
                        # If purchased, write transaction DB entry
                        if will_purchase:
                            txn_id = f"TXN_LIVE_{str(uuid.uuid4())[:8].upper()}"
                            basket_val = round(random.uniform(150.0, 4500.0), 2)
                            txn = TransactionDB(
                                transaction_id=txn_id,
                                store_id=store_id,
                                timestamp=now,
                                basket_value_inr=basket_val
                            )
                            db.add(txn)
                            # print(f"[Sim] Customer {visitor_id} purchased: {txn_id} (INR {basket_val})")
                            
                        # Exit the store
                        info['session_seq'] += 1
                        store_exit = EventDB(
                            event_id=str(uuid.uuid4()),
                            store_id=store_id,
                            camera_id="CAM_ENTRY_02",
                            visitor_id=visitor_id,
                            event_type="EXIT",
                            timestamp=now,
                            zone_id=None,
                            dwell_ms=0,
                            is_staff=False,
                            confidence=round(random.uniform(0.92, 0.98), 2),
                            queue_depth=None,
                            sku_zone=None,
                            session_seq=info['session_seq']
                        )
                        db.add(store_exit)
                        safe_commit(db)
                        
                        # Remove from active shoppers
                        active_shoppers.pop(visitor_id)
                        # print(f"[Sim] Customer {visitor_id} exited store")
                        
                elif action == 'staff_action':
                    # Occasional staff movement event
                    staff_id = f"VIS_staff_0{random.randint(1,3)}"
                    event = EventDB(
                        event_id=str(uuid.uuid4()),
                        store_id=store_id,
                        camera_id=random.choice(["CAM_ENTRY_02", "CAM_MAIN_02", "CAM_BILL_02"]),
                        visitor_id=staff_id,
                        event_type=random.choice(["ENTRY", "ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT", "EXIT"]),
                        timestamp=now,
                        zone_id=random.choice(["SKINCARE", "HAIRCARE", "BILLING", None]),
                        dwell_ms=random.randint(5000, 45000),
                        is_staff=True,
                        confidence=0.99,
                        queue_depth=None,
                        sku_zone=None,
                        session_seq=random.randint(1, 15)
                    )
                    db.add(event)
                    safe_commit(db)
                    # print(f"[Sim] Staff {staff_id} moved around")
                    
        except OperationalError as e:
            if db:
                db.rollback()
            print(f"[Sim Error] {e}")
            time.sleep(1)
        except Exception as e:
            if db:
                db.rollback()
            print(f"[Sim Error] {e}")
        finally:
            if db:
                db.close()
            
        # Run every 8 seconds to reduce SQLite write pressure
        time.sleep(8)

def start_live_simulator():
    """Starts the real-time store simulation in a daemon thread."""
    t = threading.Thread(target=simulate_realtime_traffic, daemon=True)
    t.start()
