from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

UI_DIR = Path(os.environ.get("UI_DIR", ""))
if not UI_DIR or not Path(UI_DIR).is_dir():
    for candidate in (
        Path(__file__).resolve().parent.parent / "ui",
        Path(__file__).resolve().parent.parent.parent.parent / "ui",
    ):
        if candidate.is_dir():
            UI_DIR = candidate
            break
    else:
        UI_DIR = Path(__file__).resolve().parent.parent / "ui"
else:
    UI_DIR = Path(UI_DIR)


def create_app(settings=None) -> FastAPI:
    from operator_ui.run import Settings

    settings = settings or Settings()
    app = FastAPI(title="operator-ui", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    if UI_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=UI_DIR), name="assets")

    @app.get("/")
    async def index():
        index_path = UI_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse({"error": "ui not found", "path": str(UI_DIR)}, status_code=404)

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_core(path: str, request: Request):
        return await _proxy(settings.core_url, f"/{path}", request)

    @app.api_route("/sim/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_sim(path: str, request: Request):
        return await _proxy(settings.simulator_url, f"/v1/{path}", request)

    @app.websocket("/ws/core")
    async def ws_core_proxy(ws: WebSocket):
        await _ws_proxy(ws, settings.core_url.replace("http", "ws") + "/v1/ws/operator")

    @app.websocket("/ws/sim")
    async def ws_sim_proxy(ws: WebSocket):
        await _ws_proxy(ws, settings.simulator_url.replace("http", "ws") + "/v1/ws/scenario")

    return app


async def _proxy(base: str, path: str, request: Request) -> Response:
    url = f"{base.rstrip('/')}{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            request.method,
            url,
            content=body,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        )
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


async def _ws_proxy(client_ws: WebSocket, upstream_url: str) -> None:
    import websockets

    await client_ws.accept()
    try:
        async with websockets.connect(upstream_url) as upstream:
            async def to_client():
                async for msg in upstream:
                    await client_ws.send_text(msg)

            async def to_upstream():
                while True:
                    msg = await client_ws.receive_text()
                    await upstream.send(msg)

            import asyncio

            await asyncio.gather(to_client(), to_upstream())
    except Exception as exc:
        logger.warning("ws proxy failed: %s", exc)
        await client_ws.close()

