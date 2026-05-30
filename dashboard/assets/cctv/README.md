# CCTV footage (your dataset)

## Installed dataset

Extracted from: `CCTV Footage-20260529T160731Z-3-00144614ea.zip`

| Dashboard camera | Source file | Local path |
|------------------|-------------|------------|
| CAM_ENTRY | CAM 1.mp4 | `/assets/cctv/entry.mp4` |
| CAM_MAIN | CAM 2.mp4 | `/assets/cctv/main_floor.mp4` |
| CAM_BILL | CAM 3.mp4 | `/assets/cctv/billing.mp4` |
| (extra) | CAM 4.mp4 | `/assets/cctv/cam4.mp4` |
| (extra) | CAM 5.mp4 | `/assets/cctv/cam5.mp4` |

Files are **hard-linked** to `_extracted/CCTV Footage/` (no extra disk copy).

## View on dashboard

1. Start API: `uvicorn app.main:app --reload --port 8000`
2. Open http://localhost:8000/
3. Use **CAM_ENTRY**, **CAM_MAIN**, **CAM_BILL** buttons and PiP tiles.

Config: `dashboard/assets/cctv-feeds.json`

## Replace or add shop footage later

1. Drop new MP4s into this folder (or `stores/<STORE_ID>/`).
2. Edit `cctv-feeds.json` → set `sources` to your file paths (first match wins).
3. Hard-refresh the browser (Ctrl+Shift+R).

**Note:** Each clip is large (~70–190 MB). First load may take a few seconds; clips loop automatically.
