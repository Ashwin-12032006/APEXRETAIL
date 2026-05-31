"""
Batch-post JSONL events to POST /events/ingest (chunks of 500).
"""
import argparse
import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_events")

BATCH_SIZE = 500


def load_events(path: Path) -> list:
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("Skipping malformed line: %s", e)
    return events


def ingest(events: list, api_url: str, dry_run: bool = False) -> tuple:
    total = len(events)
    batches = [events[i : i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    logger.info("Ingesting %d events in %d batches", total, len(batches))
    success, failed = 0, 0

    for i, batch in enumerate(batches):
        if dry_run:
            logger.info("[DRY RUN] Batch %d/%d: %d events", i + 1, len(batches), len(batch))
            success += len(batch)
            continue
        try:
            resp = requests.post(f"{api_url.rstrip('/')}/events/ingest", json=batch, timeout=30)
            data = resp.json() if resp.content else {}
            if resp.status_code in (200, 201, 207):
                success += data.get("ingested", len(batch))
                failed += data.get("skipped", 0) + len(data.get("errors", []))
                logger.info("Batch %d/%d: ingested=%s", i + 1, len(batches), data.get("ingested"))
            else:
                logger.error("Batch %d failed: HTTP %s — %s", i + 1, resp.status_code, resp.text[:200])
                failed += len(batch)
        except requests.ConnectionError:
            logger.error("Cannot connect to %s — is the API running?", api_url)
            failed += len(batch)
        except Exception as e:
            logger.error("Batch %d error: %s", i + 1, e)
            failed += len(batch)
        time.sleep(0.05)

    logger.info("Ingest complete: %d accepted, %d failed/skipped", success, failed)
    return success, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest JSONL events into Store Intelligence API")
    parser.add_argument("--events", required=True, help="Path to .jsonl file")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    path = Path(args.events)
    if not path.exists():
        logger.error("Events file not found: %s", path)
        return 1

    events = load_events(path)
    if not events:
        logger.warning("No events in file")
        return 0

    ingest(events, args.api_url, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
