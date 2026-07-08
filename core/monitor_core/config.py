from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from monitor_core.models import (
    BoundTurretRef,
    CameraConfig,
    CameraRole,
    SiteConfig,
    TurretAimCalibration,
    TurretAzCorrection,
    TurretConfig,
    TurretSiteBinding,
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8080
    site_config: Path = Path("config/site.yaml")
    turret_config: Path | None = Path("config/turret.yaml")
    ai_engine_url: str = "http://localhost:8090"
    ptz_onvif_password: str = "change_me"
    sky_onvif_password: str = "change_me"
    dry_run: bool = Field(default=False, validation_alias="DRY_RUN")
    sky_detect_fps: float = 2.0
    pipeline_tick_hz: float = 10.0
    simulator_url: str = "http://localhost:8070"
    pipeline_mode: str = Field(default="live", validation_alias="PIPELINE_MODE")

    _site: SiteConfig | None = None
    _turret: TurretConfig | None = None

    def load_site(self) -> SiteConfig:
        if self._site is None:
            self._site = load_site_yaml(self.site_config)
            logger.info("Loaded site config: %s (%d cameras)", self._site.name, len(self._site.cameras))
        return self._site

    def load_turret(self) -> TurretConfig:
        if self._turret is None:
            if self.turret_config and self.turret_config.exists():
                self._turret = load_turret_yaml(self.turret_config)
            else:
                self._turret = TurretConfig()
        return self._turret

    def onvif_password_for(self, role: str) -> str:
        if role == "ptz":
            return self.ptz_onvif_password
        return self.sky_onvif_password


def load_site_yaml(path: Path) -> SiteConfig:
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    site = raw.get("site", {})
    deployment = raw.get("deployment", {})
    cameras: list[CameraConfig] = []

    for entry in raw.get("sky_cameras", []):
        cameras.append(
            CameraConfig(
                id=entry["id"],
                role=CameraRole.SKY,
                ip=entry["ip"],
                rtsp_sub=entry.get("rtsp_sub"),
                rtsp_main=entry.get("rtsp_main"),
                mount_az_deg=float(entry.get("sector_az_deg", 0)),
                mount_el_deg=float(entry.get("mount_tilt_deg", 25)),
                fov_h_deg=90.0,
                fov_v_deg=50.0,
                offset_en_m=entry.get("offset_en_m"),
                corner=entry.get("corner"),
            )
        )

    for entry in raw.get("ptz_cameras", []):
        cameras.append(
            CameraConfig(
                id=entry["id"],
                role=CameraRole.PTZ,
                ip=entry["ip"],
                rtsp_sub=entry.get("rtsp_sub"),
                rtsp_main=entry.get("rtsp_main"),
                onvif_port=int(entry.get("onvif_port", 80)),
                onvif_user=entry.get("onvif_user", "admin"),
                mount_az_deg=float(entry.get("base_az_deg", 0)),
                mount_el_deg=90.0,
                offset_en_m=entry.get("offset_en_m"),
                corner=entry.get("corner"),
            )
        )

    return SiteConfig(
        name=site.get("name", "site"),
        origin_lat=float(site.get("lat", 0)),
        origin_lon=float(site.get("lon", 0)),
        origin_alt_m=float(site.get("altitude_m", 0)),
        deployment_type=str(deployment.get("type", "cube_compact")),
        mobile=bool(deployment.get("mobile", deployment.get("type") != "building_corners")),
        bound_turrets=[
            BoundTurretRef.model_validate(entry) for entry in raw.get("bound_turrets", [])
        ],
        cameras=cameras,
    )


def load_turret_yaml(path: Path) -> TurretConfig:
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    turret = raw.get("turret", {})
    engagement = raw.get("engagement", {})
    mount = raw.get("mount", {})
    binding_raw = raw.get("site_binding", {})
    cal_raw = raw.get("aim_calibration", {})
    ip = turret.get("ip", "192.168.10.30")
    port = int(turret.get("api_port", 8030))

    az_corr = [
        TurretAzCorrection.model_validate(e) for e in cal_raw.get("az_correction", [])
    ]
    site_binding = TurretSiteBinding(
        site_id=str(binding_raw.get("site_id", "site")),
        required=bool(binding_raw.get("required", True)),
        origin_lat=float(binding_raw.get("origin_lat", 0)),
        origin_lon=float(binding_raw.get("origin_lon", 0)),
        origin_alt_m=float(binding_raw.get("origin_alt_m", 0)),
        magnetic_declination_deg=float(binding_raw.get("magnetic_declination_deg", 0)),
        offset_enu_m=list(binding_raw.get("offset_enu_m", mount.get("offset_enu_m", [0, 0, 0]))),
        base_az_deg=float(binding_raw.get("base_az_deg", mount.get("base_az_deg", 0))),
    )
    aim_calibration = TurretAimCalibration(
        pan_zero_offset_deg=float(cal_raw.get("pan_zero_offset_deg", 0)),
        tilt_zero_offset_deg=float(cal_raw.get("tilt_zero_offset_deg", 0)),
        bore_offset_az_deg=float(
            cal_raw.get("bore_offset_az_deg", raw.get("camera", {}).get("bore_offset_az_deg", 0))
        ),
        bore_offset_el_deg=float(
            cal_raw.get("bore_offset_el_deg", raw.get("camera", {}).get("bore_offset_el_deg", 0))
        ),
        az_correction=az_corr,
        calibrated_at=cal_raw.get("calibrated_at"),
        calibrated_by=cal_raw.get("calibrated_by"),
    )

    return TurretConfig(
        id=str(turret.get("id", "turret-01")),
        enabled=bool(turret.get("enabled", False)),
        controller_url=f"http://{ip}:{port}",
        standalone_capable=bool(turret.get("standalone_capable", True)),
        site_binding=site_binding,
        aim_calibration=aim_calibration,
        park_az_deg=float(mount.get("park_az_deg", 0)),
        park_el_deg=float(mount.get("park_el_deg", 45)),
        max_range_m=float(engagement.get("range_max_m", 50)),
        min_range_m=float(engagement.get("range_min_m", 10)),
        min_confidence=float(engagement.get("min_class_confidence", 0.85)),
        allowed_classes=list(engagement.get("allowed_classes", ["drone"])),
        heartbeat_timeout_ms=int(raw.get("safety", {}).get("heartbeat_timeout_ms", 500)),
        track_forward_hz=float(raw.get("tracking", {}).get("track_loop_hz", 20)),
        sector_az_min_deg=float(raw.get("safety", {}).get("sector_az_min_deg", 0)),
        sector_az_max_deg=float(raw.get("safety", {}).get("sector_az_max_deg", 360)),
        priority=int(turret.get("priority", 0)),
    )
