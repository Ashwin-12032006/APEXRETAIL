#!/usr/bin/env python3
"""
Run YOLOv8 detection on all 5 local CCTV MP4 files and ingest events to the API.

Usage:
  python scripts/run_yolo_five_cameras.py
  python scripts/run_yolo_five_cameras.py --frame-stride 6 --api-url http://localhost:8000
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Map MP4 filename → API camera_id (STORE_BLR_002 layout)
CAMERA_MAP = [
    ("entry.mp4", "CAM_ENTRY_02"),
    ("main_floor.mp4", "CAM_MAIN_02"),
    ("billing.mp4", "CAM_BILL_02"),
    ("cam4.mp4", "CAM_MAIN_02"),
    ("cam5.mp4", "CAM_BILL_02"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLO pipeline for 5 CCTV feeds")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"))
    parser.add_argument("--store-id", default="STORE_BLR_002")
    parser.add_argument(
        "--cctv-dir",
        default=str(ROOT / "dashboard" / "assets" / "cctv"),
        help="Folder containing entry.mp4, main_floor.mp4, etc.",
    )
    parser.add_argument("--frame-stride", type=int, default=4, help="Higher = faster, less dense")
    parser.add_argument("--ingest-only", action="store_true", help="Only ingest existing JSONL")
    args = parser.parse_args()

    cctv_dir = Path(args.cctv_dir)
    layout = str(ROOT / "data" / "store_layout.json")
    events_dir = ROOT / "events"
    events_dir.mkdir(exist_ok=True)

    if args.ingest_only:
        from pipeline.ingest_events import ingest, load_events

        for filename, camera_id in CAMERA_MAP:
            out = events_dir / f"{args.store_id}_{camera_id}_{filename}.jsonl"
            if out.exists():
                ingest(load_events(out), args.api_url)
        return 0

    try:
        from pipeline.detect import VideoProcessor, CV_AVAILABLE
    except ImportError:
        print("Install: pip install opencv-python-headless ultralytics")
        return 1

    if not CV_AVAILABLE:
        print("OpenCV/Ultralytics not available.")
        return 1

    for filename, camera_id in CAMERA_MAP:
        video = cctv_dir / filename
        if not video.is_file():
            print(f"[skip] Missing {video}")
            continue

        out = events_dir / f"{args.store_id}_{camera_id}_{filename}.jsonl"
        print(f"\n{'='*60}\nProcessing {filename} as {camera_id}\nOutput: {out}\n{'='*60}")

        vp = VideoProcessor(
            store_id=args.store_id,
            camera_id=camera_id,
            layout_path=layout,
            output_path=str(out),
            api_url=args.api_url,
        )
        rc = vp.process_video(str(video), frame_stride=max(1, args.frame_stride))
        if rc:
            print(f"Warning: detect returned {rc} for {filename}")

        from pipeline.ingest_events import ingest, load_events

        if out.exists():
            events = load_events(out)
            if events:
                ingest(events, args.api_url)

    print("\nDone. All 5 cameras processed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
