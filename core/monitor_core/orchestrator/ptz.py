from __future__ import annotations

import logging
import math

from monitor_core.models import CameraConfig, PtzCue, TrackState
from monitor_core.onvif.client import OnvifPtzClient, PtzPool, _normalize_angle_deg

logger = logging.getLogger(__name__)


class PtzOrchestrator:
    """
    Select up to two PTZ cameras and cue them toward active tracks.
    Pair selection by mount az proximity (corner assignment from site.yaml).
    """

    def __init__(self, ptz_cameras: list[CameraConfig], pool: PtzPool) -> None:
        self.ptz_cameras = ptz_cameras
        self.pool = pool

    def select_pair(self, track: TrackState) -> tuple[str, str | None]:
        ranked = sorted(
            self.ptz_cameras,
            key=lambda c: _angular_distance_deg(c.mount_az_deg, 0.0, track.az_deg, track.el_deg),
        )
        primary = ranked[0].id
        secondary = ranked[1].id if len(ranked) > 1 else None
        return primary, secondary

    def cue_for_track(self, track: TrackState, *, zoom: float = 0.35) -> list[PtzCue]:
        primary_id, secondary_id = self.select_pair(track)
        cues = [
            PtzCue(camera_id=primary_id, az_deg=track.az_deg, el_deg=track.el_deg, zoom=zoom),
        ]
        if secondary_id:
            cues.append(
                PtzCue(camera_id=secondary_id, az_deg=track.az_deg, el_deg=track.el_deg, zoom=zoom),
            )
        return cues

    def apply_cues(self, cues: list[PtzCue]) -> None:
        for cue in cues:
            try:
                self.pool.cue(cue.camera_id, cue.az_deg, cue.el_deg, cue.zoom)
            except Exception:
                logger.warning("PTZ cue failed: %s", cue.camera_id)

    def cue_tracks(self, tracks: list[TrackState], *, max_tracks: int = 2) -> None:
        for track in tracks[:max_tracks]:
            cues = self.cue_for_track(track)
            self.apply_cues(cues)


def _angular_distance_deg(az1: float, el1: float, az2: float, el2: float) -> float:
    d_az = abs(_normalize_angle_deg(az1 - az2))
    d_el = abs(el1 - el2)
    return math.sqrt(d_az * d_az + d_el * d_el)
