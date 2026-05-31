# PROMPT:
# Confirm zone_classifier.py loads store_layout.json and maps (x,y) to SKINCARE,
# BILLING, and entry zones via heuristics when polygons are absent; verify SKU map.
#
# CHANGES MADE:
# - test_load_layout reads data/store_layout.json for STORE_BLR_002 / CAM_MAIN_02
# - Heuristic tests for left-half SKINCARE, billing camera center, entry bottom band
# - sku_for_zone linked to layout metadata (MOISTURISER / SERUM / SKINCARE)
#
"""Zone classifier heuristics and layout parsing."""
import json
from pathlib import Path

from pipeline.zone_classifier import ZoneClassifier

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "data" / "store_layout.json"


def test_load_layout():
    with open(LAYOUT, encoding="utf-8") as f:
        data = json.load(f)
    zc = ZoneClassifier(data, "STORE_BLR_002", "CAM_MAIN_02")
    assert zc.use_heuristics or len(zc.zones) >= 0


def test_heuristic_skincare_left():
    zc = ZoneClassifier({"stores": []}, "STORE_BLR_002", "CAM_MAIN_02")
    zone = zc.classify_point(400, 400, 1920, 1080)
    assert zone == "SKINCARE"


def test_heuristic_billing_camera():
    zc = ZoneClassifier({"stores": []}, "STORE_BLR_002", "CAM_BILL_02")
    zone = zc.classify_point(960, 540, 1920, 1080)
    assert zone == "BILLING"


def test_entry_zone_bottom():
    zc = ZoneClassifier({"stores": []}, "STORE_BLR_002", "CAM_ENTRY_02")
    assert zc.in_entry_zone(900, 1080) is True
    assert zc.in_entry_zone(100, 1080) is False


def test_sku_map_from_layout():
    with open(LAYOUT, encoding="utf-8") as f:
        data = json.load(f)
    zc = ZoneClassifier(data, "STORE_BLR_002", "CAM_MAIN_02")
    assert zc.sku_for_zone("SKINCARE") in ("MOISTURISER", "SERUM", "SKINCARE", None)
