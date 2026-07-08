from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone

from monitor_core.models import CameraConfig, SkyDetectionResult, TrackState
from monitor_core.onvif.client import az_el_from_pixel

logger = logging.getLogger(__name__)


class TrackerService:
    """
    Merge sky detections into coarse tracks (az/el).
    Full multi-camera fusion and Kalman filter — later iteration.
    """

    def __init__(self, cameras: dict[str, CameraConfig], *, merge_deg: float = 8.0) -> None:
        self._cameras = cameras
        self.merge_deg = merge_deg
        self._tracks: dict[str, TrackState] = {}

    @property
    def tracks(self) -> list[TrackState]:
        return list(self._tracks.values())

    def update(self, detections: dict[str, SkyDetectionResult]) -> list[TrackState]:
        now = datetime.now(timezone.utc)
        observations: list[tuple[str, str, float, float, float]] = []

        for cam_id, result in detections.items():
            camera = self._cameras.get(cam_id)
            if not camera:
                continue
            for det in result.detections:
                az, el = az_el_from_pixel(camera, det.bbox.x, det.bbox.y)
                observations.append((cam_id, det.class_name, det.confidence, az, el))

        matched: set[str] = set()
        for cam_id, class_name, conf, az, el in observations:
            track_id = self._match_track(az, el, matched)
            if track_id:
                t = self._tracks[track_id]
                t.az_deg = az
                t.el_deg = el
                t.confidence = max(t.confidence, conf)
                t.class_name = class_name if conf >= t.confidence else t.class_name
                if cam_id not in t.source_cameras:
                    t.source_cameras.append(cam_id)
                t.updated_at = now
            else:
                track_id = f"trk-{uuid.uuid4().hex[:8]}"
                self._tracks[track_id] = TrackState(
                    id=track_id,
                    class_name=class_name,
                    confidence=conf,
                    az_deg=az,
                    el_deg=el,
                    updated_at=now,
                    source_cameras=[cam_id],
                )
                matched.add(track_id)

        self._prune_stale(now)
        return self.tracks

    def _match_track(self, az: float, el: float, matched: set[str]) -> str | None:
        best_id: str | None = None
        best_dist = self.merge_deg
        for tid, track in self._tracks.items():
            if tid in matched:
                continue
            d = _angular_distance_deg(track.az_deg, track.el_deg, az, el)
            if d < best_dist:
                best_dist = d
                best_id = tid
        if best_id:
            matched.add(best_id)
        return best_id

    def _prune_stale(self, now: datetime, max_age_s: float = 5.0) -> None:
        stale = [
            tid
            for tid, t in self._tracks.items()
            if (now - t.updated_at).total_seconds() > max_age_s
        ]
        for tid in stale:
            del self._tracks[tid]


def _angular_distance_deg(az1: float, el1: float, az2: float, el2: float) -> float:
    d_az = abs(az1 - az2)
    if d_az > 180:
        d_az = 360 - d_az
    d_el = abs(el1 - el2)
    return math.sqrt(d_az * d_az + d_el * d_el)
