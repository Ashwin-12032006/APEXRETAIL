"""CCTV feed URLs — local MP4, env overrides (Cloudinary), Drive fallback."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

CAM_FILES = {
    "CAM1": "entry.mp4",
    "CAM2": "main_floor.mp4",
    "CAM3": "billing.mp4",
    "CAM4": "cam4.mp4",
    "CAM5": "cam5.mp4",
}

ENV_KEYS = {
    "CAM1": "CCTV_CAM1_URL",
    "CAM2": "CCTV_CAM2_URL",
    "CAM3": "CCTV_CAM3_URL",
    "CAM4": "CCTV_CAM4_URL",
    "CAM5": "CCTV_CAM5_URL",
}

DRIVE_FALLBACK = {
    "CAM1": "https://drive.google.com/file/d/1z6qK2164vaomm1-9RJfyyEqeWj9cFOGn/view",
    "CAM2": "https://drive.google.com/file/d/1vwNzH5wR8IN1H_me8l7UXc-UciM5hVJL/view",
    "CAM3": "https://drive.google.com/file/d/1yWZgawwER4Ab0ICk3bVmIP7N-kdy_qHS/view",
    "CAM4": "https://drive.google.com/file/d/1Q9_uFYDJ-u9DZqodu4YWkVUcUmeLM86A/view",
    "CAM5": "https://drive.google.com/file/d/1FRcr78s78bx4KczdFuAFMkc1eEBFTtH6/view",
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "dashboard" / "assets" / "cctv-feeds.json"


def _sources_for_cam(cam: str) -> List[str]:
    sources: List[str] = []
    env_url = os.getenv(ENV_KEYS.get(cam, ""), "").strip()
    if env_url:
        sources.append(env_url)
    local = f"/assets/cctv/{CAM_FILES[cam]}"
    if local not in sources:
        sources.append(local)
    drive = DRIVE_FALLBACK.get(cam)
    if drive and drive not in sources:
        sources.append(drive)
    return sources


def build_cctv_feeds() -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if CONFIG_PATH.is_file():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

    default_block: Dict[str, Any] = {}
    store_block: Dict[str, Any] = {}
    for cam, fname in CAM_FILES.items():
        default_block[cam] = {
            "label": cam.replace("CAM", "CAM "),
            "sources": _sources_for_cam(cam),
        }
        store_block[cam] = {"sources": _sources_for_cam(cam)}

    data.setdefault("camera_map", dict(CAM_FILES))
    data["default"] = default_block
    data.setdefault("stores", {})
    data["stores"]["STORE_BLR_002"] = store_block
    data["_note"] = (
        "Set CCTV_CAM1_URL … CCTV_CAM5_URL for direct MP4 (face detection on deploy). "
        "Upload: python scripts/upload_cctv_cloudinary.py"
    )
    return data


@router.get("/cctv/feeds.json")
def cctv_feeds_json():
    return JSONResponse(build_cctv_feeds())
