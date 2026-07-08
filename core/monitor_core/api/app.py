from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from monitor_core.api.ws import register_ws_routes, start_operator_broadcast, stop_operator_broadcast
from monitor_core.config import Settings
from monitor_core.models import TurretArmCommand, TurretSafeCommand
from monitor_core.operation_mode import OperationMode
from monitor_core.pipeline.coordinator import PipelineCoordinator

logger = logging.getLogger(__name__)

_coordinator: PipelineCoordinator | None = None


def get_coordinator() -> PipelineCoordinator:
    if _coordinator is None:
        raise RuntimeError("Pipeline not initialized")
    return _coordinator


class ModeRequest(BaseModel):
    mode: OperationMode


class CalibStartRequest(BaseModel):
    scope: str = Field(description="sky_overlap | ptz_zoom | site_origin | turret_boresight")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _coordinator
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
        _coordinator = PipelineCoordinator(settings)
        await _coordinator.start()
        start_operator_broadcast(get_coordinator)
        yield
        await stop_operator_broadcast()
        await _coordinator.stop()

    app = FastAPI(title="Dron Monitoring — monitor-core", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_ws_routes(app, get_coordinator)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/status")
    async def status():
        return (await get_coordinator().system_status()).model_dump()

    @app.get("/v1/mode")
    async def get_mode():
        c = get_coordinator()
        return {"mode": c.operation_mode.value}

    @app.post("/v1/mode")
    async def set_mode(req: ModeRequest):
        await get_coordinator().set_mode(req.mode)
        return {"ok": True, "mode": req.mode.value}

    @app.get("/v1/site/layout")
    async def site_layout():
        return get_coordinator().site_layout()

    @app.get("/v1/tracks")
    async def tracks():
        return [t.model_dump(mode="json") for t in get_coordinator().tracker.tracks]

    @app.get("/v1/targets")
    async def targets():
        return [t.model_dump(mode="json") for t in get_coordinator().geolocated_targets]

    @app.post("/v1/ptz/{camera_id}/goto")
    async def ptz_goto(camera_id: str, az_deg: float, el_deg: float, zoom: float = 0.0):
        get_coordinator().ptz_pool.cue(camera_id, az_deg, el_deg, zoom)
        return {"ok": True}

    @app.post("/v1/calibration/auto/start")
    async def calib_start(req: CalibStartRequest):
        return get_coordinator().calibration.start(req.scope)

    @app.get("/v1/calibration/jobs")
    async def calib_jobs():
        return get_coordinator().calibration.list_jobs()

    @app.get("/v1/calibration/jobs/{job_id}")
    async def calib_job(job_id: str):
        job = get_coordinator().calibration.get(job_id)
        if not job:
            raise HTTPException(404, "job not found")
        return job

    @app.get("/v1/turrets")
    async def list_turrets():
        fleet = get_coordinator().turret_fleet
        rows = []
        for unit in fleet.units:
            cfg = unit.config
            rows.append(
                {
                    "id": cfg.id,
                    "enabled": cfg.enabled,
                    "controller_url": cfg.controller_url,
                    "offset_enu_m": cfg.site_binding.offset_enu_m,
                    "binding_ok": unit.binding_ok,
                    "max_range_m": cfg.max_range_m,
                    "sector_az_deg": [cfg.sector_az_min_deg, cfg.sector_az_max_deg],
                }
            )
        return rows

    @app.get("/v1/turrets/{turret_id}/status")
    async def turret_status_by_id(turret_id: str):
        unit = get_coordinator().turret_fleet.get(turret_id)
        if unit is None:
            raise HTTPException(404, f"turret not found: {turret_id}")
        status = await unit.client.status()
        if status is None:
            return {"id": turret_id, "reachable": False}
        return {"id": turret_id, **status.model_dump()}

    @app.post("/v1/turrets/{turret_id}/arm")
    async def turret_arm_by_id(turret_id: str, body: dict):
        ok = await get_coordinator().turret_fleet.arm(turret_id, TurretArmCommand.model_validate(body))
        return {"ok": ok, "turret_id": turret_id}

    @app.post("/v1/turrets/{turret_id}/safe")
    async def turret_safe_by_id(turret_id: str, body: dict):
        ok = await get_coordinator().turret_fleet.safe(turret_id, TurretSafeCommand.model_validate(body))
        return {"ok": ok, "turret_id": turret_id}

    @app.post("/v1/turret/arm")
    async def turret_arm_all(body: dict):
        ok = await get_coordinator().turret_fleet.arm(None, TurretArmCommand.model_validate(body))
        return {"ok": ok}

    @app.post("/v1/turret/safe")
    async def turret_safe_all(body: dict):
        ok = await get_coordinator().turret_fleet.safe(None, TurretSafeCommand.model_validate(body))
        return {"ok": ok}

    @app.get("/v1/turret/status")
    async def turret_status_legacy():
        return await list_turrets()

    @app.get("/v1/turret/binding")
    async def turret_binding_legacy():
        fleet = get_coordinator().turret_fleet
        return [
            {
                "id": u.config.id,
                "site_id": u.config.site_binding.site_id,
                "offset_enu_m": u.config.site_binding.offset_enu_m,
                "binding_ok": u.binding_ok,
                "binding_error": u.binding_error,
                "calibrated_at": u.config.aim_calibration.calibrated_at,
            }
            for u in fleet.units
        ]

    return app
