#!/usr/bin/env python3
"""
Upload local CCTV MP4s to Cloudinary and print Vercel/Railway env vars.

Requires: pip install cloudinary
Env: CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME

Usage:
  python scripts/upload_cctv_cloudinary.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CCTV_DIR = ROOT / "dashboard" / "assets" / "cctv"

FILES = {
    "CCTV_CAM1_URL": "entry.mp4",
    "CCTV_CAM2_URL": "main_floor.mp4",
    "CCTV_CAM3_URL": "billing.mp4",
    "CCTV_CAM4_URL": "cam4.mp4",
    "CCTV_CAM5_URL": "cam5.mp4",
}


def main() -> int:
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        print("Install: pip install cloudinary", file=sys.stderr)
        return 1

    if not os.getenv("CLOUDINARY_URL"):
        print("Set CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD_NAME", file=sys.stderr)
        print("Free account: https://cloudinary.com/users/register_free", file=sys.stderr)
        return 1

    cloudinary.config(secure=True)
    print("\n=== Uploading CCTV clips to Cloudinary ===\n")

    for env_key, filename in FILES.items():
        path = CCTV_DIR / filename
        if not path.is_file():
            print(f"SKIP {filename} (not found)")
            continue
        print(f"Uploading {filename} ({path.stat().st_size // (1024 * 1024)} MB)...")
        result = cloudinary.uploader.upload(
            str(path),
            resource_type="video",
            folder="apexretail/cctv",
            public_id=filename.replace(".mp4", ""),
            overwrite=True,
        )
        url = result.get("secure_url") or result.get("url")
        print(f"{env_key}={url}\n")

    print("=== Add these to Vercel (API project) → Environment Variables ===")
    print("Then redeploy API and hard-refresh the CV lab page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
