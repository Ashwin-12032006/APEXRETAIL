"""
Staff vs customer classification via HSV uniform color on torso ROI.

Purplle / Apex retail staff typically wear solid dark or branded uniforms
(black coat, navy, purple). Customers wear varied casual attire.

Design: color clustering on middle-third of bounding box — no labelled
training data required, runs on CPU without GPU.
"""
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger("staff_detector")

# Tunable HSV profiles — black coat is primary signal for this deployment
STAFF_COLOR_PROFILES = [
    {"name": "black_coat", "lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 55])},
    {"name": "navy", "lower": np.array([100, 80, 20]), "upper": np.array([130, 255, 100])},
    {"name": "purple_uniform", "lower": np.array([120, 80, 80]), "upper": np.array([160, 255, 255])},
]

STAFF_COLOR_COVERAGE_THRESHOLD = 0.35


class StaffDetector:
    """Classify person as staff (uniform) or customer from frame + bbox."""

    def __init__(self, color_profiles: Optional[list] = None, coverage_threshold: float = None):
        self.profiles = color_profiles or STAFF_COLOR_PROFILES
        self.coverage_threshold = coverage_threshold or STAFF_COLOR_COVERAGE_THRESHOLD

    def classify(self, frame: np.ndarray, bbox: np.ndarray) -> bool:
        x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return False

        bbox_h = y2 - y1
        torso_y1 = y1 + bbox_h // 3
        torso_y2 = y1 + (2 * bbox_h) // 3
        torso_roi = frame[torso_y1:torso_y2, x1:x2]
        if torso_roi.size == 0:
            return False
        return self._color_match(torso_roi)

    def classify_with_score(self, frame: np.ndarray, bbox: np.ndarray) -> tuple:
        """Returns (is_staff, confidence 0-1)."""
        x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return False, 0.0

        bbox_h = y2 - y1
        torso_y1 = y1 + bbox_h // 3
        torso_y2 = y1 + (2 * bbox_h) // 3
        torso_roi = frame[torso_y1:torso_y2, x1:x2]
        if torso_roi.size == 0:
            return False, 0.0

        score = self._max_coverage(torso_roi)
        return score >= self.coverage_threshold, min(1.0, score)

    def _color_match(self, roi: np.ndarray) -> bool:
        return self._max_coverage(roi) >= self.coverage_threshold

    def _max_coverage(self, roi: np.ndarray) -> float:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        total = roi.shape[0] * roi.shape[1]
        if total == 0:
            return 0.0
        best = 0.0
        for profile in self.profiles:
            mask = cv2.inRange(hsv, profile["lower"], profile["upper"])
            coverage = float(np.sum(mask > 0)) / total
            if coverage > best:
                best = coverage
                logger.debug("Staff profile %s coverage=%.2f", profile["name"], coverage)
        return best
