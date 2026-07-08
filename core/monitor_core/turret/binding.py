from __future__ import annotations

import logging
import math

from monitor_core.models import (
    SiteConfig,
    TurretAimCalibration,
    TurretAzCorrection,
    TurretBindCommand,
    TurretConfig,
    TurretSiteBinding,
)

logger = logging.getLogger(__name__)


def validate_site_binding(site: SiteConfig, turret: TurretConfig) -> tuple[bool, str]:
    """Проверка совпадения site_id и согласованности origin."""
    binding = turret.site_binding
    if binding.site_id != site.name:
        return False, f"site_id mismatch: turret={binding.site_id!r} site={site.name!r}"

    tol = 1e-6
    if abs(binding.origin_lat - site.origin_lat) > tol:
        return False, "origin_lat differs between site.yaml and turret site_binding"
    if abs(binding.origin_lon - site.origin_lon) > tol:
        return False, "origin_lon differs between site.yaml and turret site_binding"
    if abs(binding.origin_alt_m - site.origin_alt_m) > tol:
        return False, "origin_alt_m differs between site.yaml and turret site_binding"

    return True, "ok"


def build_bind_command(site: SiteConfig, turret: TurretConfig) -> TurretBindCommand:
    """Пакет привязки для отправки на turret-controller при старте core."""
    b = turret.site_binding
    return TurretBindCommand(
        turret_id=turret.id,
        site_id=b.site_id,
        origin_lat=b.origin_lat,
        origin_lon=b.origin_lon,
        origin_alt_m=b.origin_alt_m,
        magnetic_declination_deg=b.magnetic_declination_deg,
        offset_enu_m=list(b.offset_enu_m),
        base_az_deg=b.base_az_deg,
        aim_calibration=turret.aim_calibration,
    )


def site_enu_relative(position_enu_m: list[float], offset_enu_m: list[float]) -> list[float]:
    """Позиция цели относительно узла pan/tilt турели."""
    return [
        position_enu_m[0] - offset_enu_m[0],
        position_enu_m[1] - offset_enu_m[1],
        position_enu_m[2] - offset_enu_m[2],
    ]


def enu_to_az_el_deg(e: float, n: float, u: float) -> tuple[float, float]:
    """ENU → азимут/угол места (север=0°, восток=90°)."""
    horiz = math.sqrt(e * e + n * n)
    az = math.degrees(math.atan2(e, n)) % 360.0
    el = math.degrees(math.atan2(u, horiz)) if horiz > 1e-6 else (90.0 if u > 0 else -90.0)
    return az, el


def apply_aim_calibration(
    az_deg: float,
    el_deg: float,
    calibration: TurretAimCalibration,
    *,
    for_fire: bool = False,
) -> tuple[float, float]:
    """Поправки нуля энкодеров и bore-sight."""
    az = az_deg + calibration.pan_zero_offset_deg
    el = el_deg + calibration.tilt_zero_offset_deg

    for entry in calibration.az_correction:
        if abs(el - entry.at_el_deg) <= 3.0:
            az += entry.delta_az_deg

    if for_fire:
        az += calibration.bore_offset_az_deg
        el += calibration.bore_offset_el_deg

    return az % 360.0, el


def site_target_to_cue_angles(
    position_enu_m: list[float],
    binding: TurretSiteBinding,
    calibration: TurretAimCalibration,
) -> tuple[float, float]:
    """
    Site ENU → команда pan/tilt (грубое наведение).
    Используется core для cue_az/cue_el в track и отладки.
    """
    rel = site_enu_relative(position_enu_m, binding.offset_enu_m)
    az, el = enu_to_az_el_deg(rel[0], rel[1], rel[2])
    az = (az + binding.base_az_deg) % 360.0
    return apply_aim_calibration(az, el, calibration, for_fire=False)


def is_calibration_complete(calibration: TurretAimCalibration) -> bool:
    return calibration.calibrated_at is not None


def distance_from_mount_m(position_enu_m: list[float], offset_enu_m: list[float]) -> float:
    """Наклонная дальность от узла pan/tilt турели до цели."""
    rel = site_enu_relative(position_enu_m, offset_enu_m)
    return math.sqrt(rel[0] ** 2 + rel[1] ** 2 + rel[2] ** 2)


def target_az_from_mount_deg(position_enu_m: list[float], offset_enu_m: list[float]) -> float:
    rel = site_enu_relative(position_enu_m, offset_enu_m)
    az, _ = enu_to_az_el_deg(rel[0], rel[1], rel[2])
    return az


def az_in_sector(az_deg: float, az_min: float, az_max: float) -> bool:
    az = az_deg % 360.0
    if az_min <= az_max:
        return az_min <= az <= az_max
    return az >= az_min or az <= az_max
