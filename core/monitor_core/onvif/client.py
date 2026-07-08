from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from monitor_core.models import CameraConfig

logger = logging.getLogger(__name__)


@dataclass
class PtzStatus:
    camera_id: str
    pan_norm: float
    tilt_norm: float
    zoom_norm: float
    pan_deg: float | None = None
    tilt_deg: float | None = None


class OnvifPtzClient:
    """ONVIF PTZ wrapper for Hikvision DS-2DE4A425IWG-E."""

    def __init__(
        self,
        camera: CameraConfig,
        password: str,
        *,
        dry_run: bool = False,
    ) -> None:
        self.camera = camera
        self.password = password
        self.dry_run = dry_run
        self._camera = None
        self._ptz = None

    def connect(self) -> None:
        if self.dry_run:
            logger.info("ONVIF dry-run: skip connect %s", self.camera.id)
            return
        try:
            from onvif import ONVIFCamera

            self._camera = ONVIFCamera(
                self.camera.ip,
                self.camera.onvif_port,
                self.camera.onvif_user,
                self.password,
            )
            self._ptz = self._camera.create_ptz_service()
            logger.info("ONVIF connected: %s (%s)", self.camera.id, self.camera.ip)
        except Exception:
            logger.exception("ONVIF connect failed: %s", self.camera.id)
            raise

    def disconnect(self) -> None:
        self._camera = None
        self._ptz = None

    def absolute_move(self, pan_norm: float, tilt_norm: float, zoom_norm: float) -> None:
        pan_norm = _clamp(pan_norm, -1.0, 1.0)
        tilt_norm = _clamp(tilt_norm, -1.0, 1.0)
        zoom_norm = _clamp(zoom_norm, 0.0, 1.0)

        if self.dry_run or self._ptz is None:
            logger.debug(
                "ONVIF dry-run move %s pan=%.3f tilt=%.3f zoom=%.3f",
                self.camera.id,
                pan_norm,
                tilt_norm,
                zoom_norm,
            )
            return

        from onvif import ONVIFError

        try:
            token = self._get_profile_token()
            request = self._ptz.create_type("AbsoluteMove")
            request.ProfileToken = token
            request.Position.PanTilt.x = pan_norm
            request.Position.PanTilt.y = tilt_norm
            request.Position.Zoom.x = zoom_norm
            self._ptz.AbsoluteMove(request)
        except ONVIFError:
            logger.exception("ONVIF AbsoluteMove failed: %s", self.camera.id)
            raise

    def goto_az_el(self, az_deg: float, el_deg: float, zoom: float = 0.0) -> None:
        """Map site az/el to ONVIF normalized coords using mount offset."""
        rel_az = _normalize_angle_deg(az_deg - self.camera.mount_az_deg)
        rel_el = el_deg - self.camera.mount_el_deg
        pan_norm = rel_az / 180.0
        tilt_norm = _clamp(rel_el / 90.0, -1.0, 1.0)
        self.absolute_move(pan_norm, tilt_norm, zoom)

    def get_status(self) -> PtzStatus:
        if self.dry_run or self._ptz is None:
            return PtzStatus(
                camera_id=self.camera.id,
                pan_norm=0.0,
                tilt_norm=0.0,
                zoom_norm=0.0,
            )

        token = self._get_profile_token()
        status = self._ptz.GetStatus({"ProfileToken": token})
        pan = float(status.Position.PanTilt.x)
        tilt = float(status.Position.PanTilt.y)
        zoom = float(status.Position.Zoom.x) if status.Position.Zoom else 0.0
        return PtzStatus(
            camera_id=self.camera.id,
            pan_norm=pan,
            tilt_norm=tilt,
            zoom_norm=zoom,
            pan_deg=pan * 180.0 + self.camera.mount_az_deg,
            tilt_deg=tilt * 90.0 + self.camera.mount_el_deg,
        )

    def _get_profile_token(self) -> str:
        if self._camera is None:
            raise RuntimeError("ONVIF not connected")
        media = self._camera.create_media_service()
        profiles = media.GetProfiles()
        if not profiles:
            raise RuntimeError(f"No ONVIF profiles on {self.camera.id}")
        return profiles[0].token


class PtzPool:
    """Pool of ONVIF clients for all PTZ cameras."""

    def __init__(self, cameras: list[CameraConfig], password: str, *, dry_run: bool = False) -> None:
        self._clients = {
            cam.id: OnvifPtzClient(cam, password, dry_run=dry_run) for cam in cameras
        }

    @property
    def camera_ids(self) -> list[str]:
        return list(self._clients.keys())

    def connect_all(self) -> None:
        for client in self._clients.values():
            try:
                client.connect()
            except Exception:
                logger.warning("PTZ %s offline", client.camera.id)

    def disconnect_all(self) -> None:
        for client in self._clients.values():
            client.disconnect()

    def get(self, camera_id: str) -> OnvifPtzClient:
        return self._clients[camera_id]

    def cue(self, camera_id: str, az_deg: float, el_deg: float, zoom: float = 0.0) -> None:
        self._clients[camera_id].goto_az_el(az_deg, el_deg, zoom)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalize_angle_deg(deg: float) -> float:
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


def az_el_from_pixel(
    camera: CameraConfig,
    px: float,
    py: float,
    *,
    image_w: float = 1.0,
    image_h: float = 1.0,
) -> tuple[float, float]:
    """Rough az/el from normalized bbox center (sky camera)."""
    fov_h = camera.fov_h_deg or 90.0
    fov_v = camera.fov_v_deg or 50.0
    cx = (px + 0.5) - 0.5
    cy = 0.5 - (py + 0.5)
    rel_az = cx * fov_h
    rel_el = cy * fov_v
    az = _normalize_angle_deg(camera.mount_az_deg + rel_az)
    el = _clamp(camera.mount_el_deg + rel_el, -10.0, 85.0)
    return az, el


def enu_distance_m(position: list[float]) -> float:
    x, y, z = position[0], position[1], position[2]
    return math.sqrt(x * x + y * y + z * z)
