from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from monitor_core.models import Detection, DetectionBBox, SkyDetectionResult

logger = logging.getLogger(__name__)


class SimFeedService:
    """Poll scenario-simulator detections when pipeline runs in simulation mode."""

    def __init__(self, simulator_url: str, *, poll_hz: float = 5.0) -> None:
        self.simulator_url = simulator_url.rstrip("/")
        self.interval_s = 1.0 / poll_hz
        self._latest: dict[str, SkyDetectionResult] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def latest_detections(self) -> dict[str, SkyDetectionResult]:
        return dict(self._latest)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name="sim_feed")
        logger.info("sim_feed started → %s", self.simulator_url)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._fetch_once()
            except Exception:
                logger.exception("sim_feed poll failed")
            await asyncio.sleep(self.interval_s)

    async def _fetch_once(self) -> None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.simulator_url}/v1/feed/detections")
            resp.raise_for_status()
            raw = resp.json()
        now = datetime.now(timezone.utc)
        parsed: dict[str, SkyDetectionResult] = {}
        for cam_id, entry in raw.items():
            dets = []
            for d in entry.get("detections", []):
                dets.append(
                    Detection(
                        class_name=d["class"],
                        confidence=float(d["confidence"]),
                        bbox=DetectionBBox(**d["bbox"]),
                    )
                )
            ts = entry.get("timestamp")
            timestamp = datetime.fromisoformat(ts) if ts else now
            if not timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            parsed[cam_id] = SkyDetectionResult(
                camera_id=cam_id,
                timestamp=timestamp,
                detections=dets,
            )
        self._latest = parsed
