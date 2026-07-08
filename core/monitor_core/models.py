from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class BoundTurretRef(BaseModel):
    """Запись в site.yaml → отдельный файл конфигурации турели."""
    id: str
    config: str
    enabled: bool = True
    optional: bool = True


class CameraRole(StrEnum):
    SKY = "sky"
    PTZ = "ptz"


class CameraConfig(BaseModel):
    id: str
    role: CameraRole
    ip: str
    rtsp_sub: str | None = None
    rtsp_main: str | None = None
    onvif_port: int = 80
    onvif_user: str = "admin"
    mount_az_deg: float = 0.0
    mount_el_deg: float = 0.0
    fov_h_deg: float | None = None
    fov_v_deg: float | None = None
    offset_en_m: list[float] | None = None
    corner: str | None = None


class SiteConfig(BaseModel):
    name: str = "site"
    origin_lat: float = 0.0
    origin_lon: float = 0.0
    origin_alt_m: float = 0.0
    deployment_type: str = "cube_compact"
    mobile: bool = True
    bound_turrets: list[BoundTurretRef] = Field(default_factory=list)
    cameras: list[CameraConfig] = Field(default_factory=list)

    def sky_cameras(self) -> list[CameraConfig]:
        return [c for c in self.cameras if c.role == CameraRole.SKY]

    def ptz_cameras(self) -> list[CameraConfig]:
        return [c for c in self.cameras if c.role == CameraRole.PTZ]


class TurretAzCorrection(BaseModel):
    at_el_deg: float
    delta_az_deg: float


class TurretSiteBinding(BaseModel):
    site_id: str
    required: bool = True
    origin_lat: float = 0.0
    origin_lon: float = 0.0
    origin_alt_m: float = 0.0
    magnetic_declination_deg: float = 0.0
    offset_enu_m: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    base_az_deg: float = 0.0


class TurretAimCalibration(BaseModel):
    pan_zero_offset_deg: float = 0.0
    tilt_zero_offset_deg: float = 0.0
    bore_offset_az_deg: float = 0.0
    bore_offset_el_deg: float = 0.0
    az_correction: list[TurretAzCorrection] = Field(default_factory=list)
    calibrated_at: str | None = None
    calibrated_by: str | None = None


class TurretConfig(BaseModel):
    id: str = "turret-01"
    enabled: bool = False
    controller_url: str = "http://192.168.10.30:8030"
    standalone_capable: bool = True
    site_binding: TurretSiteBinding = Field(
        default_factory=lambda: TurretSiteBinding(site_id="site")
    )
    aim_calibration: TurretAimCalibration = Field(default_factory=TurretAimCalibration)
    park_az_deg: float = 0.0
    park_el_deg: float = 45.0
    max_range_m: float = 50.0
    min_range_m: float = 10.0
    min_confidence: float = 0.85
    allowed_classes: list[str] = Field(default_factory=lambda: ["drone"])
    heartbeat_timeout_ms: int = 500
    track_forward_hz: float = 20.0
    sector_az_min_deg: float = 0.0
    sector_az_max_deg: float = 360.0
    priority: int = 0


class DetectionBBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class Detection(BaseModel):
    class_name: str = Field(alias="class")
    confidence: float
    bbox: DetectionBBox

    model_config = {"populate_by_name": True}


class SkyDetectionResult(BaseModel):
    camera_id: str
    timestamp: datetime
    detections: list[Detection] = Field(default_factory=list)


class TrackState(BaseModel):
    id: str
    class_name: str = "unknown"
    confidence: float = 0.0
    az_deg: float
    el_deg: float
    position_enu_m: list[float] | None = None
    velocity_enu_m_s: list[float] | None = None
    updated_at: datetime
    source_cameras: list[str] = Field(default_factory=list)


class PtzCue(BaseModel):
    camera_id: str
    az_deg: float
    el_deg: float
    zoom: float = 0.0


class GeolocatedTarget(BaseModel):
    target_id: str
    class_name: str
    confidence: float
    lat: float
    lon: float
    alt_m: float
    position_enu_m: list[float]
    velocity_enu_m_s: list[float] | None = None
    updated_at: datetime


class TurretTrackCommand(BaseModel):
    target_id: str
    site_id: str
    frame: Literal["site_enu"] = "site_enu"
    class_name: str = Field(alias="class")
    confidence: float
    position_enu_m: list[float]
    velocity_enu_m_s: list[float]
    valid_until_ms: int
    # Подсказка для грубого наведения (core считает с учётом binding + calibration)
    cue_az_deg: float | None = None
    cue_el_deg: float | None = None

    model_config = {"populate_by_name": True}


class TurretBindCommand(BaseModel):
    """Синхронизация привязки monitor-core → turret-controller при старте."""
    turret_id: str
    site_id: str
    origin_lat: float
    origin_lon: float
    origin_alt_m: float
    magnetic_declination_deg: float
    offset_enu_m: list[float]
    base_az_deg: float
    aim_calibration: TurretAimCalibration


class TurretArmCommand(BaseModel):
    enabled: bool
    operator_token: str | None = None


class TurretSafeCommand(BaseModel):
    reason: str = "manual"


class TurretStatus(BaseModel):
    state: Literal["SAFE", "IDLE", "TRACK", "ARMED", "FAULT"]
    az_deg: float = 0.0
    el_deg: float = 0.0
    pressure_bar: float | None = None
    rounds_loaded: int | None = None
    faults: list[str] = Field(default_factory=list)
    last_track_id: str | None = None
    bound_site_id: str | None = None
    binding_ok: bool = False
    calibration_ok: bool = False


class TurretUnitStatus(BaseModel):
    id: str
    enabled: bool
    controller_url: str
    binding_ok: bool = False
    binding_error: str | None = None
    reachable: bool | None = None
    offset_enu_m: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])


class SystemStatus(BaseModel):
    pipeline_running: bool
    operation_mode: str = "live"
    sky_cameras_online: int
    ptz_cameras_online: int
    active_tracks: int
    turret_enabled: bool
    turret_count: int = 0
    turrets: list[TurretUnitStatus] = Field(default_factory=list)
    # устаревшие поля — первый модуль или агрегат
    turret_reachable: bool | None = None
    turret_binding_ok: bool | None = None
