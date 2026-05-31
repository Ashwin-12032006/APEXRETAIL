#!/bin/sh
set -e
mkdir -p /app/data /app/events
# Named volume on Windows: avoid bind-mount SQLite disk I/O errors; seed from image on first run
if [ ! -f /app/data/store_layout.json ]; then
  cp -a /app/data-seed/. /app/data/
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
