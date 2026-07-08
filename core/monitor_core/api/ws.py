from __future__ import annotations

import asyncio
import logging
from typing import Callable

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

_clients: set[WebSocket] = set()
_broadcast_task: asyncio.Task | None = None


def start_operator_broadcast(get_coordinator: Callable) -> None:
    global _broadcast_task
    if _broadcast_task is None or _broadcast_task.done():
        _broadcast_task = asyncio.create_task(_broadcast_loop(get_coordinator))


async def stop_operator_broadcast() -> None:
    global _broadcast_task
    if _broadcast_task:
        _broadcast_task.cancel()
        try:
            await _broadcast_task
        except asyncio.CancelledError:
            pass
        _broadcast_task = None


def register_ws_routes(app, get_coordinator: Callable) -> None:
    @app.websocket("/v1/ws/operator")
    async def ws_operator(ws: WebSocket):
        await ws.accept()
        _clients.add(ws)
        try:
            from monitor_core.api.ws import _frame_payload

            coord = get_coordinator()
            await ws.send_json(await _frame_payload(coord))
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            _clients.discard(ws)


async def _broadcast_loop(get_coordinator: Callable) -> None:
    from monitor_core.api.ws import _frame_payload

    while True:
        await asyncio.sleep(0.25)
        if not _clients:
            continue
        try:
            coord = get_coordinator()
            payload = await _frame_payload(coord)
        except Exception:
            continue
        dead: list[WebSocket] = []
        for ws in _clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _clients.discard(ws)


async def _frame_payload(coord) -> dict:
    sim_objects = []
    if coord.operation_mode.value == "simulation":
        sim_objects = await coord.fetch_sim_objects()
    return {
        "type": "frame",
        "mode": coord.operation_mode.value,
        "tracks": [t.model_dump(mode="json") for t in coord.tracker.tracks],
        "targets": [t.model_dump(mode="json") for t in coord.geolocated_targets],
        "sim_objects": sim_objects,
        "status": (await coord.system_status()).model_dump(),
    }
