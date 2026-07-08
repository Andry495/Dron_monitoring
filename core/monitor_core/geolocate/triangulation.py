from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from monitor_core.models import CameraConfig, GeolocatedTarget, SiteConfig, TrackState

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_000.0


class GeolocateService:
    """
    Triangulate target position from two PTZ sight lines.
    v1: ray intersection in local ENU; lat/lon from site origin.
    """

    def __init__(self, site: SiteConfig) -> None:
        self.site = site

    def triangulate(
        self,
        track: TrackState,
        ray_a: tuple[str, float, float],
        ray_b: tuple[str, float, float],
    ) -> GeolocatedTarget | None:
        """
        ray_a/b: (camera_id, az_deg, el_deg) from PTZ status or cue.
        """
        cam_a = _find_camera(self.site, ray_a[0])
        cam_b = _find_camera(self.site, ray_b[0])
        if not cam_a or not cam_b:
            return None

        origin = (0.0, 0.0, 0.0)
        dir_a = _ray_from_az_el(ray_a[1], ray_a[2])
        dir_b = _ray_from_az_el(ray_b[1], ray_b[2])

        point = _closest_point_between_rays(origin, dir_a, origin, dir_b)
        if point is None:
            return None

        x, y, z = point
        if z < 1.0:
            return None

        lat, lon, alt = _enu_to_geodetic(
            x, y, z,
            self.site.origin_lat,
            self.site.origin_lon,
            self.site.origin_alt_m,
        )

        return GeolocatedTarget(
            target_id=track.id,
            class_name=track.class_name,
            confidence=track.confidence,
            lat=lat,
            lon=lon,
            alt_m=alt,
            position_enu_m=[x, y, z],
            velocity_enu_m_s=track.velocity_enu_m_s,
            updated_at=datetime.now(timezone.utc),
        )


def _find_camera(site: SiteConfig, camera_id: str) -> CameraConfig | None:
    for cam in site.cameras:
        if cam.id == camera_id:
            return cam
    return None


def _ray_from_az_el(az_deg: float, el_deg: float) -> tuple[float, float, float]:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    x = math.cos(el) * math.sin(az)
    y = math.cos(el) * math.cos(az)
    z = math.sin(el)
    return x, y, z


def _closest_point_between_rays(
    p1: tuple[float, float, float],
    d1: tuple[float, float, float],
    p2: tuple[float, float, float],
    d2: tuple[float, float, float],
) -> tuple[float, float, float] | None:
    """Least-squares midpoint of two infinite lines (simplified ENU)."""
    w0 = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
    a = _dot(d1, d1)
    b = _dot(d1, d2)
    c = _dot(d2, d2)
    d = _dot(d1, w0)
    e = _dot(d2, w0)
    denom = a * c - b * b
    if abs(denom) < 1e-9:
        return None
    sc = (b * e - c * d) / denom
    tc = (a * e - b * d) / denom
    p_a = (p1[0] + sc * d1[0], p1[1] + sc * d1[1], p1[2] + sc * d1[2])
    p_b = (p2[0] + tc * d2[0], p2[1] + tc * d2[1], p2[2] + tc * d2[2])
    return (
        (p_a[0] + p_b[0]) / 2,
        (p_a[1] + p_b[1]) / 2,
        (p_a[2] + p_b[2]) / 2,
    )


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _enu_to_geodetic(
    e: float,
    n: float,
    u: float,
    lat0: float,
    lon0: float,
    alt0: float,
) -> tuple[float, float, float]:
    lat_rad = math.radians(lat0)
    d_lat = n / EARTH_RADIUS_M
    d_lon = e / (EARTH_RADIUS_M * math.cos(lat_rad))
    lat = lat0 + math.degrees(d_lat)
    lon = lon0 + math.degrees(d_lon)
    alt = alt0 + u
    return lat, lon, alt
