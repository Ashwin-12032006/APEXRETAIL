# CCTV dummy & real shop videos

Place MP4 or WebM files here so the dashboard plays **same-origin** footage (faces visible, face-crop overlays work).

## Quick setup (dummy retail footage)

1. Download 3 free clips (people in supermarket / beauty store / checkout), for example from [Mixkit](https://mixkit.co/free-stock-video/shopping/).
2. Rename and copy into this folder:

| File | Camera | Suggested content |
|------|--------|-------------------|
| `entry.mp4` | CAM_ENTRY | Shoppers entering / mall aisle |
| `main_floor.mp4` | CAM_MAIN | Aisle / cosmetics browsing |
| `billing.mp4` | CAM_BILL | Checkout / card payment |

3. Hard-refresh the dashboard: http://localhost:8000/

## Per-store real footage (later)

Copy your shop recordings to:

```text
dashboard/assets/cctv/stores/<STORE_ID>/entry.mp4
dashboard/assets/cctv/stores/<STORE_ID>/main_floor.mp4
dashboard/assets/cctv/stores/<STORE_ID>/billing.mp4
```

Example: `stores/STORE_BLR_002/entry.mp4`

Paths are listed in `dashboard/cctv-feeds.json` under `stores`. You can also add **HTTPS/RTSP proxy URLs** as extra entries in `sources` (browser needs direct MP4/WebM URL).

## Config file

Edit `dashboard/cctv-feeds.json` to change source order or add stores. First URL that loads wins.
