# PROMPT:
# Validate staff_detector.py classifies black-coat torso (store uniform) vs colorful
# customer clothing using HSV on the middle-third ROI; skip suite if OpenCV missing.
#
# CHANGES MADE:
# - Synthetic BGR frames with black torso + lighter face region
# - assert staff or score threshold for uniform frame
# - assert not staff for bright casual shirt (control case)
# - pytest.importorskip("cv2") for environments without OpenCV
#
"""Staff detector — black coat / uniform HSV."""
import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from pipeline.staff_detector import StaffDetector


def test_black_torso_detected_as_staff():
    det = StaffDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Black coat torso region
    frame[200:350, 250:390] = (15, 15, 15)
    # Lighter face (should not dominate — torso is middle third)
    frame[120:200, 280:360] = (200, 180, 170)
    bbox = np.array([240, 100, 400, 400])
    is_staff, score = det.classify_with_score(frame, bbox)
    assert is_staff or score > 0.2


def test_colorful_customer_not_staff():
    det = StaffDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[200:350, 250:390] = (30, 200, 255)  # bright casual shirt
    bbox = np.array([240, 100, 400, 400])
    is_staff, _ = det.classify_with_score(frame, bbox)
    assert is_staff is False
