from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class FrameMeta:
    camera_id: str
    timestamp: datetime
    width: int
    height: int
    jpeg_bytes: bytes | None = None


class FrameSource(ABC):
    @abstractmethod
    async def grab(self) -> FrameMeta | None:
        ...


class DryRunFrameSource(FrameSource):
    """Placeholder when RTSP is unavailable (dev / dry-run)."""

    def __init__(self, camera_id: str) -> None:
        self.camera_id = camera_id

    async def grab(self) -> FrameMeta | None:
        return FrameMeta(
            camera_id=self.camera_id,
            timestamp=datetime.now(timezone.utc),
            width=1280,
            height=720,
            jpeg_bytes=None,
        )


class RtspFrameSource(FrameSource):
    """
    RTSP ingest hook. Full OpenCV/ffmpeg pipeline is added when hardware is wired.
    For now logs and returns metadata only.
    """

    def __init__(self, camera_id: str, rtsp_url: str) -> None:
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url

    async def grab(self) -> FrameMeta | None:
        logger.debug("RTSP grab %s %s", self.camera_id, self.rtsp_url)
        return FrameMeta(
            camera_id=self.camera_id,
            timestamp=datetime.now(timezone.utc),
            width=1280,
            height=720,
            jpeg_bytes=None,
        )


def create_frame_source(camera_id: str, rtsp_url: str | None, *, dry_run: bool) -> FrameSource:
    if dry_run or not rtsp_url:
        return DryRunFrameSource(camera_id)
    return RtspFrameSource(camera_id, rtsp_url)
