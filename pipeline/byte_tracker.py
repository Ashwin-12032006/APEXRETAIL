"""
ByteTrack-inspired multi-object tracker (IoU + Kalman).

Two-stage matching: high-confidence detections first, then low-confidence
recoveries through partial occlusion (billing queues, group entry).
"""
from enum import Enum
from typing import List, Optional

import numpy as np
from scipy.optimize import linear_sum_assignment


class TrackState(Enum):
    NEW = 0
    TRACKED = 1
    LOST = 2
    REMOVED = 3


class KalmanFilter:
    def __init__(self):
        dt = 1.0
        self.F = np.eye(8)
        for i in range(4):
            self.F[i, i + 4] = dt
        self.H = np.eye(4, 8)
        self.Q = np.eye(8) * 0.01
        self.R = np.eye(4) * 1.0
        self.P = np.eye(8) * 10.0
        self.x = np.zeros(8)

    def init(self, measurement: np.ndarray):
        self.x[:4] = measurement
        self.P = np.eye(8) * 10.0
        return self.x

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[:4]

    def update(self, measurement: np.ndarray):
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ (measurement - self.H @ self.x)
        self.P = (np.eye(8) - K @ self.H) @ self.P
        return self.x[:4]


class Track:
    _id_counter = 0

    def __init__(self, detection: list, score: float):
        Track._id_counter += 1
        self.track_id = Track._id_counter
        self.score = score
        self.state = TrackState.NEW
        self.age = 0
        self.hits = 1
        self.frames_lost = 0
        self.kf = KalmanFilter()
        cx, cy, w, h = self._tlbr_to_cxcywh(detection[:4])
        self.kf.init(np.array([cx, cy, w, h]))
        self._tlbr = np.array(detection[:4], dtype=float)

    @property
    def tlbr(self) -> np.ndarray:
        return self._tlbr

    def predict(self):
        pred = self.kf.predict()
        self._tlbr = self._cxcywh_to_tlbr(pred)
        self.age += 1

    def update(self, detection: list, score: float):
        cx, cy, w, h = self._tlbr_to_cxcywh(detection[:4])
        updated = self.kf.update(np.array([cx, cy, w, h]))
        self._tlbr = self._cxcywh_to_tlbr(updated)
        self.score = score
        self.hits += 1
        self.frames_lost = 0
        self.state = TrackState.TRACKED

    def mark_lost(self):
        self.frames_lost += 1
        self.state = TrackState.LOST

    @staticmethod
    def _tlbr_to_cxcywh(tlbr):
        x1, y1, x2, y2 = tlbr
        return (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1

    @staticmethod
    def _cxcywh_to_tlbr(cxcywh):
        cx, cy, w, h = cxcywh
        return np.array([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])


class ByteTracker:
    def __init__(
        self,
        high_thresh: float = 0.5,
        low_thresh: float = 0.1,
        match_thresh: float = 0.8,
        max_lost: int = 30,
        min_hits: int = 3,
    ):
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.match_thresh = match_thresh
        self.max_lost = max_lost
        self.min_hits = min_hits
        self.tracked_tracks: List[Track] = []
        self.lost_tracks: List[Track] = []

    def update(self, detections: list) -> List[Track]:
        if not detections:
            for t in self.tracked_tracks:
                t.mark_lost()
            self.lost_tracks.extend(self.tracked_tracks)
            self.tracked_tracks = []
            self.lost_tracks = [t for t in self.lost_tracks if t.frames_lost <= self.max_lost]
            return self._active()

        dets = np.array(detections, dtype=float)
        high_dets = dets[dets[:, 4] >= self.high_thresh]
        low_dets = dets[(dets[:, 4] >= self.low_thresh) & (dets[:, 4] < self.high_thresh)]

        for t in self.tracked_tracks + self.lost_tracks:
            t.predict()

        matched_h, unmatched_tracks_h, unmatched_dets_h = self._match(self.tracked_tracks, high_dets)
        activated, refound = [], []

        for ti, di in matched_h:
            self.tracked_tracks[ti].update(high_dets[di].tolist(), float(high_dets[di, 4]))
            if self.tracked_tracks[ti].hits >= self.min_hits:
                self.tracked_tracks[ti].state = TrackState.TRACKED
            activated.append(self.tracked_tracks[ti])

        unmatched_objs = [self.tracked_tracks[i] for i in unmatched_tracks_h]
        matched_l, still_unmatched, _ = self._match(unmatched_objs, low_dets)
        for ti, di in matched_l:
            unmatched_objs[ti].update(low_dets[di].tolist(), float(low_dets[di, 4]))
            activated.append(unmatched_objs[ti])
        for i in still_unmatched:
            unmatched_objs[i].mark_lost()
            self.lost_tracks.append(unmatched_objs[i])

        unmatched_new = list(range(len(unmatched_dets_h)))
        if len(unmatched_dets_h) and len(self.lost_tracks):
            matched_r, _, unmatched_new = self._match(self.lost_tracks, high_dets[unmatched_dets_h])
            for ti, di in matched_r:
                idx = unmatched_dets_h[di]
                self.lost_tracks[ti].update(high_dets[idx].tolist(), float(high_dets[idx, 4]))
                self.lost_tracks[ti].state = TrackState.TRACKED
                refound.append(self.lost_tracks[ti])

        remaining = (
            high_dets[unmatched_dets_h][unmatched_new]
            if len(unmatched_new)
            else np.empty((0, 6), dtype=float)
        )
        new_tracks = [Track(det.tolist(), float(det[4])) for det in remaining if det[4] >= self.high_thresh]

        self.lost_tracks = [
            t for t in self.lost_tracks
            if t.state != TrackState.TRACKED and t.frames_lost <= self.max_lost
        ]
        self.tracked_tracks = activated + refound + new_tracks
        return self._active()

    def _match(self, tracks: list, detections: np.ndarray):
        if len(tracks) == 0 or len(detections) == 0:
            return [], list(range(len(tracks))), list(range(len(detections)))
        iou = self._iou_batch(np.array([t.tlbr for t in tracks]), detections[:, :4])
        cost = 1 - iou
        row_ind, col_ind = linear_sum_assignment(cost)
        matched, unmatched_t, unmatched_d = [], [], []
        matched_rows, matched_cols = set(), set()
        for r, c in zip(row_ind, col_ind):
            if cost[r, c] <= (1 - self.match_thresh):
                matched.append((r, c))
                matched_rows.add(r)
                matched_cols.add(c)
        unmatched_t = [i for i in range(len(tracks)) if i not in matched_rows]
        unmatched_d = [i for i in range(len(detections)) if i not in matched_cols]
        return matched, unmatched_t, unmatched_d

    @staticmethod
    def _iou_batch(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        area_a = (boxes_a[:, 2] - boxes_a[:, 0]) * (boxes_a[:, 3] - boxes_a[:, 1])
        area_b = (boxes_b[:, 2] - boxes_b[:, 0]) * (boxes_b[:, 3] - boxes_b[:, 1])
        inter_x1 = np.maximum(boxes_a[:, None, 0], boxes_b[None, :, 0])
        inter_y1 = np.maximum(boxes_a[:, None, 1], boxes_b[None, :, 1])
        inter_x2 = np.minimum(boxes_a[:, None, 2], boxes_b[None, :, 2])
        inter_y2 = np.minimum(boxes_a[:, None, 3], boxes_b[None, :, 3])
        inter = np.maximum(0, inter_x2 - inter_x1) * np.maximum(0, inter_y2 - inter_y1)
        union = area_a[:, None] + area_b[None, :] - inter
        return inter / (union + 1e-6)

    def _active(self) -> List[Track]:
        return [
            t for t in self.tracked_tracks + self.lost_tracks
            if t.state in (TrackState.TRACKED, TrackState.NEW, TrackState.LOST) and t.hits >= 1
        ]
