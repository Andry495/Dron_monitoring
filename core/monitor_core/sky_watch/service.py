from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from monitor_core.ai.client import AiEngineClient
from monitor_core.ingest.rtsp import FrameSource, create_frame_source
from monitor_core.models import CameraConfig, SkyDetectionResult

logger = logging.getLogger(__name__)


class SkyWatchService:
    """Poll sky camera substreams and run detection via ai-engine."""

    def __init__(
        self,
        cameras: list[CameraConfig],
        ai: AiEngineClient,
        *,
        fps: float = 2.0,
        dry_run: bool = False,
    ) -> None:
        self.cameras = cameras
        self.ai = ai
        self.interval_s = 1.0 / fps
        self._sources: dict[str, FrameSource] = {
            cam.id: create_frame_source(cam.id, cam.rtsp_sub, dry_run=dry_run) for cam in cameras
        }
        self._latest: dict[str, SkyDetectionResult] = {}
        self._running = False

    @property
    def latest_detections(self) -> dict[str, SkyDetectionResult]:
        return dict(self._latest)

    async def run(self) -> None:
        self._running = True
        logger.info("sky_watch started (%d cameras, %.1f FPS)", len(self.cameras), 1.0 / self.interval_s)
        while self._running:
            await asyncio.gather(*(self._poll_camera(cam) for cam in self.cameras))
            await asyncio.sleep(self.interval_s)

    def stop(self) -> None:
        self._running = False

    async def _poll_camera(self, camera: CameraConfig) -> None:
        source = self._sources[camera.id]
        frame = await source.grab()
        if frame is None:
            return
        result = await self.ai.detect(
            camera.id,
            width=frame.width,
            height=frame.height,
            jpeg_bytes=frame.jpeg_bytes,
        )
        if not result.timestamp.tzinfo:
            result.timestamp = result.timestamp.replace(tzinfo=timezone.utc)
        self._latest[camera.id] = result
