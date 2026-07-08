from __future__ import annotations

import math
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class AzCorrection(BaseModel):
    at_el_deg: float
    delta_az_deg: float


class AimCalibration(BaseModel):
    pan_zero_offset_deg: float = 0.0
    tilt_zero_offset_deg: float = 0.0
    bore_offset_az_deg: float = 0.0
    bore_offset_el_deg: float = 0.0
    az_correction: list[AzCorrection] = Field(default_factory=list)
    calibrated_at: str | None = None
    calibrated_by: str | None = None


class BindCommand(BaseModel):
    turret_id: str
    site_id: str
    origin_lat: float
    origin_lon: float
    origin_alt_m: float
    magnetic_declination_deg: float = 0.0
    offset_enu_m: list[float]
    base_az_deg: float = 0.0
    aim_calibration: AimCalibration


class TrackCommand(BaseModel):
    target_id: str
    site_id: str = ""
    frame: str = "site_enu"
    class_name: str = Field(alias="class")
    confidence: float
    position_enu_m: list[float]
    velocity_enu_m_s: list[float]
    valid_until_ms: int
    cue_az_deg: float | None = None
    cue_el_deg: float | None = None

    model_config = {"populate_by_name": True}


class ArmCommand(BaseModel):
    enabled: bool
    operator_token: str | None = None


class SafeCommand(BaseModel):
    reason: str = "manual"


class TurretStatus(BaseModel):
    state: Literal["SAFE", "IDLE", "TRACK", "ARMED", "FAULT"] = "SAFE"
    az_deg: float = 0.0
    el_deg: float = 0.0
    pressure_bar: float = 10.0
    rounds_loaded: int = 1
    faults: list[str] = Field(default_factory=list)
    last_track_id: str | None = None
    bound_site_id: str | None = None
    binding_ok: bool = False
    calibration_ok: bool = False
    last_heartbeat_ms: int = 0


_binding: BindCommand | None = None


def _apply_calibration(az: float, el: float, cal: AimCalibration) -> tuple[float, float]:
    az += cal.pan_zero_offset_deg
    el += cal.tilt_zero_offset_deg
    for entry in cal.az_correction:
        if abs(el - entry.at_el_deg) <= 3.0:
            az += entry.delta_az_deg
    return az % 360.0, el


def _position_to_angles(position: list[float], binding: BindCommand) -> tuple[float, float]:
    ox, oy, oz = binding.offset_enu_m
    e, n, u = position[0] - ox, position[1] - oy, position[2] - oz
    horiz = math.sqrt(e * e + n * n)
    az = math.degrees(math.atan2(e, n)) % 360.0
    el = math.degrees(math.atan2(u, horiz)) if horiz > 1e-6 else 0.0
    az = (az + binding.base_az_deg) % 360.0
    return _apply_calibration(az, el, binding.aim_calibration)


def create_app() -> FastAPI:
    app = FastAPI(title="Turret Controller Simulator", version="0.1.0")
    status = TurretStatus()

    @app.post("/v1/turret/bind")
    async def bind(cmd: BindCommand):
        global _binding
        _binding = cmd
        status.bound_site_id = cmd.site_id
        status.binding_ok = True
        status.calibration_ok = cmd.aim_calibration.calibrated_at is not None
        status.last_heartbeat_ms = int(time.time() * 1000)
        return {"ok": True, "site_id": cmd.site_id, "turret_id": cmd.turret_id}

    @app.get("/v1/turret/binding")
    async def get_binding():
        if _binding is None:
            return {"bound": False}
        return {"bound": True, "binding": _binding.model_dump()}

    @app.get("/v1/turret/status")
    async def get_status():
        status.last_heartbeat_ms = int(time.time() * 1000)
        return status.model_dump()

    @app.post("/v1/turret/track")
    async def track(cmd: TrackCommand):
        if _binding is None:
            raise HTTPException(409, "turret not bound — POST /v1/turret/bind first")
        if cmd.site_id and cmd.site_id != _binding.site_id:
            raise HTTPException(409, f"site_id mismatch: {cmd.site_id!r} != {_binding.site_id!r}")

        status.state = "TRACK"
        status.last_track_id = cmd.target_id
        status.last_heartbeat_ms = int(time.time() * 1000)

        if cmd.cue_az_deg is not None and cmd.cue_el_deg is not None:
            status.az_deg = cmd.cue_az_deg
            status.el_deg = cmd.cue_el_deg
        elif cmd.position_enu_m:
            status.az_deg, status.el_deg = _position_to_angles(cmd.position_enu_m, _binding)

        return {"ok": True}

    @app.post("/v1/turret/arm")
    async def arm(cmd: ArmCommand):
        if not status.binding_ok:
            raise HTTPException(409, "turret not bound")
        status.state = "ARMED" if cmd.enabled else "IDLE"
        return {"ok": True}

    @app.post("/v1/turret/safe")
    async def safe(cmd: SafeCommand):
        status.state = "SAFE"
        status.last_track_id = None
        return {"ok": True, "reason": cmd.reason}

    return app
