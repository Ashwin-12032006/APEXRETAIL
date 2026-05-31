"""
Map pixel coordinates to named store zones using store_layout.json.

Supports polygon-based zones (challenge format) and heuristic fallback
when layout only lists zone_id + camera_id (current Apex layout file).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger("zone_classifier")

ENTRY_FRACTION = 0.20


class ZoneClassifier:
    """Point-in-polygon zone lookup with camera-specific heuristics fallback."""

    def __init__(self, store_layout: dict, store_id: str, camera_id: str):
        self.store_id = store_id
        self.camera_id = camera_id
        self.zones = self._parse_polygon_zones(store_layout, store_id, camera_id)
        self.sku_map = self._parse_sku_map(store_layout, store_id)
        self.use_heuristics = len(self.zones) == 0
        if self.use_heuristics:
            logger.info("No polygons for %s/%s — using heuristic zones", store_id, camera_id)

    @classmethod
    def from_layout_file(cls, layout_path: str, store_id: str, camera_id: str) -> "ZoneClassifier":
        path = Path(layout_path)
        if not path.exists():
            logger.warning("Layout file missing: %s", layout_path)
            return cls({"stores": []}, store_id, camera_id)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(data, store_id, camera_id)

    def _find_store(self, layout: dict, store_id: str) -> Optional[dict]:
        for store in layout.get("stores", []):
            if store.get("store_id") == store_id:
                return store
        return None

    def _parse_polygon_zones(self, layout: dict, store_id: str, camera_id: str) -> List[dict]:
        store = self._find_store(layout, store_id)
        if not store:
            return []
        zones = []
        for zone in store.get("zones", []):
            cov = zone.get("camera_coverage", {}).get(camera_id, {})
            polygon = cov.get("polygon") if cov else zone.get("polygon")
            if polygon:
                zones.append({
                    "zone_id": zone["zone_id"],
                    "polygon": np.array(polygon, dtype=np.float32),
                    "sku_zone": self._first_sku(zone),
                })
        return zones

    def _parse_sku_map(self, layout: dict, store_id: str) -> Dict[str, str]:
        store = self._find_store(layout, store_id)
        mapping = {}
        if not store:
            return mapping
        for zone in store.get("zones", []):
            zid = zone.get("zone_id")
            sku = self._first_sku(zone)
            if zid and sku:
                mapping[zid] = sku
        return mapping

    @staticmethod
    def _first_sku(zone: dict) -> Optional[str]:
        if zone.get("sku_zone"):
            return zone["sku_zone"]
        skus = zone.get("sku_zones") or []
        return skus[0] if skus else zone.get("zone_id")

    def classify_point(self, cx: float, cy: float, frame_width: int = 1920, frame_height: int = 1080) -> Optional[str]:
        if not self.use_heuristics:
            pt = (float(cx), float(cy))
            for zone in self.zones:
                if cv2.pointPolygonTest(zone["polygon"], pt, False) >= 0:
                    return zone["zone_id"]
            return None
        return self._heuristic_zone(cx, cy, frame_width, frame_height)

    def sku_for_zone(self, zone_id: Optional[str]) -> Optional[str]:
        if not zone_id:
            return None
        return self.sku_map.get(zone_id)

    def in_entry_zone(self, cy: float, frame_height: int) -> bool:
        return cy > frame_height * (1 - ENTRY_FRACTION)

    def _heuristic_zone(self, cx: float, cy: float, fw: int, fh: int) -> Optional[str]:
        """Fallback when layout has no polygons — matches camera role."""
        cam = self.camera_id.upper()
        if "ENTRY" in cam:
            if cy > fh * 0.65:
                return "ENTRY_EXIT"
            return None
        if "MAIN" in cam or "FLOOR" in cam:
            if cx < fw * 0.5:
                return "SKINCARE"
            if cy > fh * 0.75:
                return "BILLING"
            return "HAIRCARE"
        if "BILL" in cam:
            return "BILLING"
        return None
