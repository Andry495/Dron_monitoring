from __future__ import annotations

import logging
from datetime import datetime

import httpx

from monitor_core.models import Detection, SkyDetectionResult

logger = logging.getLogger(__name__)


class AiEngineClient:
    def __init__(self, base_url: str, *, timeout_s: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_s)

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> bool:
        try:
            r = await self._client.get("/v1/health")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def detect(
        self,
        camera_id: str,
        *,
        width: int,
        height: int,
        jpeg_bytes: bytes | None = None,
    ) -> SkyDetectionResult:
        payload = {
            "camera_id": camera_id,
            "width": width,
            "height": height,
            "image_b64": None,
        }
        try:
            r = await self._client.post("/v1/detect", json=payload)
            r.raise_for_status()
            data = r.json()
            detections = [Detection.model_validate(d) for d in data.get("detections", [])]
            return SkyDetectionResult(
                camera_id=camera_id,
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
                detections=detections,
            )
        except httpx.HTTPError:
            logger.warning("ai-engine detect failed for %s", camera_id)
            return SkyDetectionResult(camera_id=camera_id, timestamp=datetime.utcnow(), detections=[])

    async def classify(
        self,
        camera_id: str,
        *,
        crop_b64: str | None = None,
    ) -> tuple[str, float]:
        payload = {"camera_id": camera_id, "crop_b64": crop_b64}
        try:
            r = await self._client.post("/v1/classify", json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("class", "unknown"), float(data.get("confidence", 0.0))
        except httpx.HTTPError:
            logger.warning("ai-engine classify failed for %s", camera_id)
            return "unknown", 0.0
