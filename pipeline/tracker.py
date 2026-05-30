import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

class StoreTracker:
    def __init__(self, store_id: str):
        self.store_id = store_id
        # Registry of active tracks: track_id -> track_state
        self.active_tracks: Dict[int, Dict[str, Any]] = {}
        # Re-ID Registry for re-entry and cross-camera correlation: visitor_id -> historical_data
        # historical_data: {"last_seen": timestamp, "last_box": (x,y), "camera_id": str, "is_staff": bool}
        self.reid_registry: Dict[str, Dict[str, Any]] = {}
        # Mapping of track_id to global visitor_id
        self.track_to_visitor: Dict[int, str] = {}
        # Queue depth counter
        self.current_queue_depth = 0

    def generate_visitor_id(self) -> str:
        # Returns format VIS_xxxxx
        return f"VIS_{uuid.uuid4().hex[:6]}"

    def check_is_staff(self, frame_patch) -> bool:
        # Real uniform detector would check color histogram or run a small classification model.
        # Here we check if visual clues match staff uniforms.
        # For simulation/mock, we assume a simple rule or default.
        return False

    def correlate_reid(self, track_id: int, current_box: Tuple[float, float], camera_id: str, is_staff: bool, timestamp_str: str) -> str:
        # Simple Re-ID: check if there's a recently disappeared visitor (within 30s)
        # near the same coordinates (e.g. threshold distance 150 pixels)
        now_ts = datetime_from_str(timestamp_str)
        
        best_visitor_id = None
        min_dist = float('inf')
        
        for vis_id, hist in list(self.reid_registry.items()):
            # Calculate time difference
            last_seen = datetime_from_str(hist["last_seen"])
            time_diff = (now_ts - last_seen).total_seconds()
            
            # Check if disappeared within last 60 seconds (handling re-entry)
            if 0 < time_diff < 60:
                # Calculate distance
                hx, hy = hist["last_box"]
                cx, cy = current_box
                dist = ((hx - cx)**2 + (hy - cy)**2)**0.5
                
                # Threshold distance of 150 pixels
                if dist < 150.0 and dist < min_dist:
                    min_dist = dist
                    best_visitor_id = vis_id

        if best_visitor_id:
            # Found matching historic visitor (REENTRY or Cross-camera)
            self.track_to_visitor[track_id] = best_visitor_id
            # Update registry
            self.reid_registry[best_visitor_id].update({
                "last_seen": timestamp_str,
                "last_box": current_box,
                "camera_id": camera_id
            })
            return best_visitor_id
        else:
            # Create a new visitor session
            visitor_id = self.generate_visitor_id()
            self.track_to_visitor[track_id] = visitor_id
            self.reid_registry[visitor_id] = {
                "last_seen": timestamp_str,
                "last_box": current_box,
                "camera_id": camera_id,
                "is_staff": is_staff
            }
            return visitor_id

    def update_track(self, track_id: int, box: Tuple[float, float, float, float], camera_id: str, zone_id: Optional[str], is_staff: bool, timestamp_str: str) -> List[Dict[str, Any]]:
        # box: (xmin, ymin, xmax, ymax)
        x_center = (box[0] + box[2]) / 2.0
        y_center = (box[1] + box[3]) / 2.0
        center = (x_center, y_center)
        
        emitted_events = []

        if track_id not in self.active_tracks:
            # New track detected
            visitor_id = self.correlate_reid(track_id, center, camera_id, is_staff, timestamp_str)
            
            # Check if this is a re-entry event
            is_reentry = False
            # If the visitor has been seen before on the ENTRY camera and is entering again
            if visitor_id in self.reid_registry and camera_id.startswith("CAM_ENTRY"):
                # We check if they previously exited
                is_reentry = True

            self.active_tracks[track_id] = {
                "visitor_id": visitor_id,
                "camera_id": camera_id,
                "current_zone": zone_id,
                "dwell_start": timestamp_str,
                "last_dwell_emit": timestamp_str,
                "is_staff": is_staff,
                "last_seen": timestamp_str,
                "session_seq": 1,
                "last_box": box
            }

            # Emit ENTRY or REENTRY event if on entry camera
            if camera_id.startswith("CAM_ENTRY"):
                event_type = "REENTRY" if is_reentry else "ENTRY"
                emitted_events.append(self.create_event(
                    event_type=event_type,
                    visitor_id=visitor_id,
                    camera_id=camera_id,
                    zone_id=None,
                    dwell_ms=0,
                    is_staff=is_staff,
                    confidence=0.9,
                    timestamp=timestamp_str,
                    session_seq=1
                ))
            
            # If they are placed in a zone immediately
            if zone_id and zone_id != "ENTRY_EXIT":
                emitted_events.append(self.create_event(
                    event_type="ZONE_ENTER",
                    visitor_id=visitor_id,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    dwell_ms=0,
                    is_staff=is_staff,
                    confidence=0.9,
                    timestamp=timestamp_str,
                    session_seq=2
                ))
                self.active_tracks[track_id]["session_seq"] = 2
        else:
            # Existing track updated
            track = self.active_tracks[track_id]
            track["last_seen"] = timestamp_str
            track["last_box"] = box
            
            visitor_id = track["visitor_id"]
            old_zone = track["current_zone"]

            # If zone changed
            if zone_id != old_zone:
                # 1. Exit old zone
                if old_zone and old_zone != "ENTRY_EXIT":
                    dwell_ms = calculate_dwell_ms(track["dwell_start"], timestamp_str)
                    emitted_events.append(self.create_event(
                        event_type="ZONE_EXIT",
                        visitor_id=visitor_id,
                        camera_id=camera_id,
                        zone_id=old_zone,
                        dwell_ms=dwell_ms,
                        is_staff=is_staff,
                        confidence=0.9,
                        timestamp=timestamp_str,
                        session_seq=track["session_seq"] + 1
                    ))
                    track["session_seq"] += 1
                
                # 2. Enter new zone
                if zone_id and zone_id != "ENTRY_EXIT":
                    track["dwell_start"] = timestamp_str
                    track["last_dwell_emit"] = timestamp_str
                    emitted_events.append(self.create_event(
                        event_type="ZONE_ENTER",
                        visitor_id=visitor_id,
                        camera_id=camera_id,
                        zone_id=zone_id,
                        dwell_ms=0,
                        is_staff=is_staff,
                        confidence=0.9,
                        timestamp=timestamp_str,
                        session_seq=track["session_seq"] + 1
                    ))
                    track["session_seq"] += 1

                    # Trigger billing queue join
                    if zone_id == "BILLING":
                        self.current_queue_depth += 1
                        emitted_events.append(self.create_event(
                            event_type="BILLING_QUEUE_JOIN",
                            visitor_id=visitor_id,
                            camera_id=camera_id,
                            zone_id="BILLING",
                            dwell_ms=0,
                            is_staff=is_staff,
                            confidence=0.9,
                            timestamp=timestamp_str,
                            session_seq=track["session_seq"] + 1,
                            queue_depth=self.current_queue_depth
                        ))
                        track["session_seq"] += 1
                
                track["current_zone"] = zone_id
            else:
                # Dwell logic (emit ZONE_DWELL every 30 seconds of continuous stay)
                if zone_id and zone_id != "ENTRY_EXIT":
                    dwell_ms = calculate_dwell_ms(track["last_dwell_emit"], timestamp_str)
                    if dwell_ms >= 30000: # 30 seconds
                        total_dwell = calculate_dwell_ms(track["dwell_start"], timestamp_str)
                        emitted_events.append(self.create_event(
                            event_type="ZONE_DWELL",
                            visitor_id=visitor_id,
                            camera_id=camera_id,
                            zone_id=zone_id,
                            dwell_ms=total_dwell,
                            is_staff=is_staff,
                            confidence=0.9,
                            timestamp=timestamp_str,
                            session_seq=track["session_seq"] + 1
                        ))
                        track["last_dwell_emit"] = timestamp_str
                        track["session_seq"] += 1

        return emitted_events

    def close_track(self, track_id: int, timestamp_str: str) -> List[Dict[str, Any]]:
        emitted_events = []
        if track_id in self.active_tracks:
            track = self.active_tracks[track_id]
            visitor_id = track["visitor_id"]
            zone_id = track["current_zone"]
            camera_id = track["camera_id"]
            is_staff = track["is_staff"]

            # Exit current zone
            if zone_id and zone_id != "ENTRY_EXIT":
                dwell_ms = calculate_dwell_ms(track["dwell_start"], timestamp_str)
                emitted_events.append(self.create_event(
                    event_type="ZONE_EXIT",
                    visitor_id=visitor_id,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    dwell_ms=dwell_ms,
                    is_staff=is_staff,
                    confidence=0.9,
                    timestamp=timestamp_str,
                    session_seq=track["session_seq"] + 1
                ))
                track["session_seq"] += 1
                if zone_id == "BILLING" and self.current_queue_depth > 0:
                    self.current_queue_depth -= 1

            # Emit EXIT event on entry camera
            if camera_id.startswith("CAM_ENTRY"):
                emitted_events.append(self.create_event(
                    event_type="EXIT",
                    visitor_id=visitor_id,
                    camera_id=camera_id,
                    zone_id=None,
                    dwell_ms=0,
                    is_staff=is_staff,
                    confidence=0.9,
                    timestamp=timestamp_str,
                    session_seq=track["session_seq"] + 1
                ))

            # Store in Re-ID registry
            self.reid_registry[visitor_id] = {
                "last_seen": timestamp_str,
                "last_box": track["last_box"][:2] if "last_box" in track else (0,0),
                "camera_id": camera_id,
                "is_staff": is_staff
            }
            # Remove from active tracks
            del self.active_tracks[track_id]

        return emitted_events

    def create_event(self, event_type: str, visitor_id: str, camera_id: str, zone_id: Optional[str], dwell_ms: int, is_staff: bool, confidence: float, timestamp: str, session_seq: int, queue_depth: Optional[int] = None) -> Dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "store_id": self.store_id,
            "camera_id": camera_id,
            "visitor_id": visitor_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "zone_id": zone_id,
            "dwell_ms": dwell_ms,
            "is_staff": is_staff,
            "confidence": confidence,
            "metadata": {
                "queue_depth": queue_depth,
                "sku_zone": get_sku_zone_from_layout(self.store_id, zone_id),
                "session_seq": session_seq
            }
        }

# --- Helpers ---

def datetime_from_str(ts_str: str) -> datetime:
    try:
        if ts_str.endswith("Z"):
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts_str)
    except Exception:
        # Return current time if parse fails
        from datetime import datetime as dt
        return dt.utcnow()

def calculate_dwell_ms(start_str: str, end_str: str) -> int:
    t_start = datetime_from_str(start_str)
    t_end = datetime_from_str(end_str)
    return int((t_end - t_start).total_seconds() * 1000)

def get_sku_zone_from_layout(store_id: str, zone_id: Optional[str]) -> Optional[str]:
    # Hardcoded mapping mirroring layouts for quick emission, fallback to default SKU zone
    if not zone_id:
        return None
    mappings = {
        "SKINCARE": "MOISTURISER",
        "HAIRCARE": "SHAMPOO",
        "COSMETICS": "LIPSTICK",
        "WELLNESS": "VITAMINS",
        "FRAGRANCE": "PERFUME",
        "BILLING": None
    }
    return mappings.get(zone_id)
