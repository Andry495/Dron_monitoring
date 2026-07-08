from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from simulator.engine import ScenarioEngine, ScenarioKind

logger = logging.getLogger(__name__)

engine = ScenarioEngine()
_ws_clients: set[WebSocket] = set()
_tick_task: asyncio.Task | None = None


class StartScenarioRequest(BaseModel):
    scenario: ScenarioKind = ScenarioKind.DRONE_APPROACH


class AutoCalibRequest(BaseModel):
    scope: str = Field(description="sky_overlap | ptz_zoom | site_origin | turret_boresight")


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _tick_task
        _tick_task = asyncio.create_task(_broadcast_loop())
        yield
        if _tick_task:
            _tick_task.cancel()

    app = FastAPI(title="Dron Monitoring — scenario-simulator", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/v1/health")
    async def health():
        return {"status": "ok", "running": engine.running}

    @app.get("/v1/scenario/state")
    async def scenario_state():
        return engine.snapshot()

    @app.post("/v1/scenario/start")
    async def scenario_start(req: StartScenarioRequest):
        engine.start(req.scenario)
        await _broadcast()
        return {"ok": True, **engine.snapshot()}

    @app.post("/v1/scenario/stop")
    async def scenario_stop():
        engine.stop()
        await _broadcast()
        return {"ok": True}

    @app.get("/v1/feed/detections")
    async def feed_detections():
        return engine.sky_detections()

    @app.post("/v1/calibration/auto/run")
    async def calibration_auto_run(req: AutoCalibRequest):
        """Stub auto-calibration — returns recommended parameter deltas."""
        steps = _auto_calibration_steps(req.scope)
        return {"ok": True, "scope": req.scope, "steps": steps}

    @app.websocket("/v1/ws/scenario")
    async def ws_scenario(ws: WebSocket):
        await ws.accept()
        _ws_clients.add(ws)
        try:
            await ws.send_json({"type": "snapshot", **engine.snapshot()})
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            _ws_clients.discard(ws)

    return app


async def _broadcast_loop() -> None:
    last = asyncio.get_event_loop().time()
    while True:
        await asyncio.sleep(0.2)
        now = asyncio.get_event_loop().time()
        engine.tick(now - last)
        last = now
        if engine.running:
            await _broadcast()


async def _broadcast() -> None:
    if not _ws_clients:
        return
    payload = {"type": "frame", **engine.snapshot()}
    dead: list[WebSocket] = []
    for ws in _ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


def _auto_calibration_steps(scope: str) -> list[dict[str, Any]]:
    catalog = {
        "sky_overlap": [
            {"id": "capture", "title": "Снимок overlap с соседней sky", "status": "done", "auto": True},
            {"id": "fit_sector", "title": "Подбор sector_az_deg / mount_tilt_deg", "status": "done", "auto": True},
            {"id": "write", "title": "Запись в site.yaml", "status": "pending", "auto": True},
        ],
        "ptz_zoom": [
            {"id": "goto_mark", "title": "ONVIF goto на калибровочную метку", "status": "done", "auto": True},
            {"id": "zoom_sweep", "title": "Съёмка HFOV по zoom", "status": "done", "auto": True},
            {"id": "curve", "title": "Построение zoom_curve", "status": "pending", "auto": True},
        ],
        "site_origin": [
            {"id": "gps", "title": "GPS центра + 4 угла", "status": "pending", "auto": False},
            {"id": "enu", "title": "Расчёт offset_en_m камер", "status": "done", "auto": True},
        ],
        "turret_boresight": [
            {"id": "cue", "title": "Наведение на мишень", "status": "done", "auto": True},
            {"id": "bore", "title": "Измерение bore_offset", "status": "pending", "auto": True},
        ],
    }
    return catalog.get(scope, [{"id": "unknown", "title": f"Неизвестный scope: {scope}", "status": "error"}])
