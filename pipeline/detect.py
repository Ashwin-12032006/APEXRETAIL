import os
import json
import sys
from typing import Dict, List, Tuple, Any

# Graceful packages check
try:
    import cv2
    import ultralytics
    from ultralytics import YOLO
    OPENCV_YOLO_AVAILABLE = True
except ImportError:
    OPENCV_YOLO_AVAILABLE = False

from pipeline.tracker import StoreTracker
from pipeline.emit import emit_event_batch

class VideoProcessor:
    def __init__(self, store_id: str, layout_path: str):
        self.store_id = store_id
        self.tracker = StoreTracker(store_id)
        self.zones_polygons = self.load_zones_polygons(layout_path)

    def load_zones_polygons(self, layout_path: str) -> Dict[str, Any]:
        # Polygons representing coordinate zones on screen.
        # In a production environment, these are set via a calibration tool.
        # Here we mock default coordinates for camera coverage layout.
        return {
            "ENTRY_EXIT": [(0, 800), (1920, 1080)], # Bottom portion of entry camera
            "SKINCARE": [(100, 100), (900, 800)],
            "HAIRCARE": [(1000, 100), (1800, 800)],
            "BILLING": [(200, 200), (1700, 900)]
        }

    def determine_zone(self, box: Tuple[float, float, float, float], camera_id: str) -> str:
        # Determine which zone the bounding box falls in based on camera ID
        x_center = (box[0] + box[2]) / 2.0
        y_center = (box[1] + box[3]) / 2.0
        
        if "ENTRY" in camera_id:
            # Entry camera maps to ENTRY_EXIT or ENTRY threshold
            if y_center > 700:
                return "ENTRY_EXIT"
            return None
        elif "MAIN" in camera_id:
            # Main camera covers Skincare, Haircare, etc.
            if x_center < 960:
                return "SKINCARE"
            return "HAIRCARE"
        elif "BILL" in camera_id:
            # Billing camera covers Billing counter
            return "BILLING"
        return None

    def process_video(self, video_path: str, camera_id: str, start_timestamp: str):
        if not OPENCV_YOLO_AVAILABLE:
            print("WARNING: OpenCV or Ultralytics YOLOv8 packages are not installed.", file=sys.stderr)
            print("Please use 'pipeline/emit_simulated.py' to feed simulated retail streams into the API.", file=sys.stderr)
            return

        print(f"Loading YOLOv8 model...")
        model = YOLO("yolov8n.pt") # Uses lightweight Nano model for performance
        
        print(f"Opening video clip: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"ERROR: Could not open video file: {video_path}", file=sys.stderr)
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
        frame_count = 0

        # Parse start_timestamp
        from pipeline.tracker import datetime_from_str
        from datetime import timedelta
        base_time = datetime_from_str(start_timestamp)

        print("Processing frames...")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            # Run YOLOv8 on class 0 (person)
            # We process every 3rd frame to optimize compute speeds
            if frame_count % 3 != 0:
                continue

            current_time = base_time + timedelta(seconds=(frame_count / fps))
            current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Run detection
            results = model(frame, classes=[0], verbose=False)
            
            # Extract tracks
            # A real deployment uses YOLO tracker: model.track(frame, persist=True)
            # Here we extract bounding boxes and use our Tracker for spatial association
            events_to_emit = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Bounding box coordinates
                    coords = box.xyxy[0].tolist() # [xmin, ymin, xmax, ymax]
                    conf = float(box.conf[0])
                    
                    if conf < 0.3: # low-confidence suppression
                        continue

                    # Mock class check for staff based on bounding box characteristics
                    is_staff = False
                    
                    # Track ID assignment
                    track_id = int(box.id[0]) if box.id is not None else 1
                    
                    zone_id = self.determine_zone(coords, camera_id)
                    
                    events = self.tracker.update_track(
                        track_id=track_id,
                        box=coords,
                        camera_id=camera_id,
                        zone_id=zone_id,
                        is_staff=is_staff,
                        timestamp_str=current_time_str
                    )
                    events_to_emit.extend(events)

            if events_to_emit:
                emit_event_batch(events_to_emit)

        # Close active tracks and emit remaining exits
        end_time_str = (base_time + timedelta(seconds=(frame_count / fps))).strftime("%Y-%m-%dT%H:%M:%SZ")
        final_events = []
        for track_id in list(self.tracker.active_tracks.keys()):
            exits = self.tracker.close_track(track_id, end_time_str)
            final_events.extend(exits)
            
        if final_events:
            emit_event_batch(final_events)

        cap.release()
        print(f"Finished processing video clip. Emitted events.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python detect.py <store_id> <camera_id> <video_path> <start_timestamp_iso>")
    else:
        store_id = sys.argv[1]
        camera_id = sys.argv[2]
        video_path = sys.argv[3]
        start_ts = sys.argv[4]
        layout = "d:/APEX RETAIL_KASH/store-intelligence/data/store_layout.json"
        
        vp = VideoProcessor(store_id, layout)
        vp.process_video(video_path, camera_id, start_ts)
