#!/usr/bin/env bash
# Purplle Store Intelligence — process CCTV clips OR run simulation
# Usage:
#   bash pipeline/run.sh                    # simulated events (default)
#   bash pipeline/run.sh clips ./clips      # YOLO pipeline on video folder
#   bash pipeline/run.sh simulate batch     # explicit simulation mode

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
MODE="${1:-simulate}"
CLIPS_DIR="${2:-$ROOT/clips}"
API_URL="${API_URL:-http://localhost:8000}"
LAYOUT="$ROOT/data/store_layout.json"
OUTPUT_DIR="$ROOT/events"
MODEL="${MODEL:-yolov8n.pt}"

echo "═══════════════════════════════════════════════════════════"
echo "  Purplle / Apex Store Intelligence Pipeline"
echo "  Mode: $MODE  |  API: $API_URL"
echo "═══════════════════════════════════════════════════════════"

cd "$ROOT"

if [ "$MODE" = "simulate" ] || [ "$MODE" = "batch" ] || [ "$MODE" = "stream" ]; then
  python -m pipeline.emit_simulated --mode "${MODE/simulate/batch}"
  echo "✅ Simulation complete. Dashboard: $API_URL"
  exit 0
fi

if [ "$MODE" = "clips" ]; then
  mkdir -p "$OUTPUT_DIR"
  if [ ! -f "$LAYOUT" ]; then
    echo "❌ store_layout.json not found at $LAYOUT"
    exit 1
  fi

  for store_dir in "$CLIPS_DIR"/STORE_*/; do
    [ -d "$store_dir" ] || continue
    store_id=$(basename "$store_dir")
    echo "▶ Store: $store_id"

    for clip in "$store_dir"*.mp4 "$store_dir"*.avi "$store_dir"*.mov; do
      [ -f "$clip" ] || continue
      filename=$(basename "$clip" | sed 's/\.[^.]*$//')
      camera_id=$(echo "$filename" | grep -oE 'CAM_[A-Z_0-9]+' || echo "CAM_ENTRY_02")
      output="$OUTPUT_DIR/${store_id}_${camera_id}.jsonl"

      echo "  📹 $camera_id → $output"
      python -m pipeline.detect \
        --video "$clip" \
        --store-id "$store_id" \
        --camera-id "$camera_id" \
        --layout "$LAYOUT" \
        --output "$output" \
        --api-url "$API_URL" || echo "  ⚠ detect failed (install ultralytics?) — trying ingest only"

      if [ -f "$output" ]; then
        python -m pipeline.ingest_events --events "$output" --api-url "$API_URL"
      fi
    done
  done

  echo "✅ Clip pipeline complete. Dashboard: $API_URL"
  exit 0
fi

echo "Unknown mode: $MODE"
echo "Use: simulate | batch | stream | clips [dir]"
exit 1
