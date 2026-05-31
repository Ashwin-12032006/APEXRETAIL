import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Set

try:
    import cv2
    import numpy as np
    from ultralytics import YOLO

    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

from pipeline.byte_tracker import ByteTracker
from pipeline.emit import EventEmitter, emit_event_batch
from pipeline.staff_detector import StaffDetector
from pipeline.tracker import StoreTracker
from pipeline.zone_classifier import ZoneClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("detect")

CONF_HIGH = 0.35  # challenge: degrade gracefully, don't drop low-conf silently


class VideoProcessor:
    """YOLOv8 + ByteTrack + staff/zone classifiers → structured events."""

    def __init__(
        self,
        store_id: str,
        camera_id: str,
        layout_path: str,
        output_path: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.store_id = store_id
        self.camera_id = camera_id
        self.store_tracker = StoreTracker(store_id)
        self.byte_tracker = ByteTracker(high_thresh=0.5, low_thresh=0.1, match_thresh=0.75)
        self.staff_detector = StaffDetector()
        self.zone_classifier = ZoneClassifier.from_layout_file(layout_path, store_id, camera_id)
        self.emitter = None
        if output_path:
            self.emitter = EventEmitter(store_id, camera_id, Path(output_path), api_url=api_url)
        self._seen_tracks: Set[int] = set()
        self._exited_visitors: Set[str] = set()

    def process_video(
        self,
        video_path: str,
        start_timestamp: Optional[str] = None,
        frame_stride: int = 2,
    ):
        if not CV_AVAILABLE:
            logger.error("OpenCV/Ultralytics not installed. Use: pip install opencv-python-headless ultralytics")
            logger.error("Fallback: python -m pipeline.emit_simulated --mode batch")
            return 1

        model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video: %s", video_path)
            return 1

        fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
        fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
        fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)
        base_time = self._parse_ts(start_timestamp)
        frame_count = 0
        batch_events: List[dict] = []

        logger.info("Processing %s (%s) @ %.1f fps", video_path, self.camera_id, fps)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_stride > 1 and frame_count % frame_stride != 0:
                continue

            current_time = base_time + timedelta(seconds=frame_count / fps)
            ts_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            results = model(frame, classes=[0], verbose=False)
            detections = []
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < 0.1:
                        continue
                    coords = box.xyxy[0].tolist()
                    detections.append(coords + [conf])

            tracks = self.byte_tracker.update(detections)
            active_ids = {t.track_id for t in tracks}

            for track in tracks:
                if track.hits < 2:
                    continue
                bbox = track.tlbr.tolist()
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                is_staff, staff_conf = self.staff_detector.classify_with_score(frame, np.array(bbox))
                zone_id = self.zone_classifier.classify_point(cx, cy, fw, fh)
                conf = max(track.score, staff_conf if is_staff else track.score)

                events = self.store_tracker.update_track(
                    track_id=track.track_id,
                    box=tuple(bbox),
                    camera_id=self.camera_id,
                    zone_id=zone_id,
                    is_staff=is_staff,
                    timestamp_str=ts_str,
                    confidence=conf,
                )
                for ev in events:
                    if ev["event_type"] == "EXIT":
                        self._exited_visitors.add(ev["visitor_id"])
                    if ev["event_type"] == "ENTRY" and ev["visitor_id"] in self._exited_visitors:
                        ev["event_type"] = "REENTRY"
                    batch_events.extend([ev])
                self._seen_tracks.add(track.track_id)

            # Close tracks no longer visible
            for tid in list(self.store_tracker.active_tracks.keys()):
                if tid not in active_ids:
                    exits = self.store_tracker.close_track(tid, ts_str)
                    for ev in exits:
                        if ev["event_type"] == "EXIT":
                            self._exited_visitors.add(ev["visitor_id"])
                    batch_events.extend(exits)

            if batch_events:
                if self.emitter:
                    for ev in batch_events:
                        self._write_via_emitter(ev)
                else:
                    emit_event_batch(batch_events)
                batch_events = []

        end_ts = (base_time + timedelta(seconds=frame_count / fps)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for tid in list(self.store_tracker.active_tracks.keys()):
            batch_events.extend(self.store_tracker.close_track(tid, end_ts))
        if batch_events:
            if self.emitter:
                for ev in batch_events:
                    self._write_via_emitter(ev)
            else:
                emit_event_batch(batch_events)

        if self.emitter:
            self.emitter.flush()

        cap.release()
        logger.info("Finished %s — frames=%d", self.camera_id, frame_count)
        return 0

    def _write_via_emitter(self, ev: dict):
        from pipeline.emit import EventType

        meta = ev.get("metadata") or {}
        self.emitter.emit(
            event_type=EventType(ev["event_type"]),
            visitor_id=ev["visitor_id"],
            zone_id=ev.get("zone_id"),
            timestamp=datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00")),
            confidence=ev["confidence"],
            is_staff=ev["is_staff"],
            session_seq=meta.get("session_seq", 1),
            dwell_ms=ev.get("dwell_ms", 0),
            queue_depth=meta.get("queue_depth"),
            sku_zone=meta.get("sku_zone"),
        )

    @staticmethod
    def _parse_ts(ts: Optional[str]) -> datetime:
        if not ts:
            return datetime.now(timezone.utc).replace(tzinfo=None)
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
        return datetime.fromisoformat(ts)


def main():
    parser = argparse.ArgumentParser(description="Purplle Store Intelligence — YOLOv8 detection pipeline")
    parser.add_argument("--video", required=True)
    parser.add_argument("--store-id", required=True)
    parser.add_argument("--camera-id", required=True)
    parser.add_argument("--layout", default="data/store_layout.json")
    parser.add_argument("--output", default=None, help="JSONL output path")
    parser.add_argument("--api-url", default=None)
    parser.add_argument("--start-ts", default=None, help="ISO UTC start timestamp for clip")
    parser.add_argument("--frame-stride", type=int, default=2, help="Process every Nth frame (4-8 faster)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    layout = args.layout if Path(args.layout).is_absolute() else str(root / args.layout)

    vp = VideoProcessor(
        store_id=args.store_id,
        camera_id=args.camera_id,
        layout_path=layout,
        output_path=args.output,
        api_url=args.api_url,
    )
    code = vp.process_video(args.video, args.start_ts, frame_stride=max(1, args.frame_stride))
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
