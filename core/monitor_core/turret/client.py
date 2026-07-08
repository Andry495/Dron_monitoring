from __future__ import annotations

import logging

import httpx

from monitor_core.models import (
    TurretArmCommand,
    TurretBindCommand,
    TurretSafeCommand,
    TurretStatus,
    TurretTrackCommand,
)

logger = logging.getLogger(__name__)


class TurretClient:
    """HTTP client to turret-controller firmware (192.168.10.30:8030)."""

    def __init__(self, base_url: str, *, timeout_s: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_s)

    async def close(self) -> None:
        await self._client.aclose()

    async def reachable(self) -> bool:
        try:
            r = await self._client.get("/v1/turret/status")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def bind(self, cmd: TurretBindCommand) -> bool:
        try:
            r = await self._client.post("/v1/turret/bind", json=cmd.model_dump())
            r.raise_for_status()
            return bool(r.json().get("ok", True))
        except httpx.HTTPError:
            logger.warning("turret bind failed for site %s", cmd.site_id)
            return False

    async def track(self, cmd: TurretTrackCommand) -> bool:
        try:
            r = await self._client.post(
                "/v1/turret/track",
                json=cmd.model_dump(by_alias=True),
            )
            r.raise_for_status()
            return True
        except httpx.HTTPError:
            logger.warning("turret track failed for %s", cmd.target_id)
            return False

    async def arm(self, cmd: TurretArmCommand) -> bool:
        try:
            r = await self._client.post("/v1/turret/arm", json=cmd.model_dump())
            r.raise_for_status()
            return True
        except httpx.HTTPError:
            logger.warning("turret arm failed")
            return False

    async def safe(self, cmd: TurretSafeCommand) -> bool:
        try:
            r = await self._client.post("/v1/turret/safe", json=cmd.model_dump())
            r.raise_for_status()
            return True
        except httpx.HTTPError:
            logger.warning("turret safe failed")
            return False

    async def status(self) -> TurretStatus | None:
        try:
            r = await self._client.get("/v1/turret/status")
            r.raise_for_status()
            return TurretStatus.model_validate(r.json())
        except httpx.HTTPError:
            return None
