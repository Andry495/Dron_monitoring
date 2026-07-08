from __future__ import annotations

import logging
import time

from monitor_core.models import GeolocatedTarget, SiteConfig, TurretConfig, TurretTrackCommand
from monitor_core.turret.binding import (
    az_in_sector,
    build_bind_command,
    distance_from_mount_m,
    is_calibration_complete,
    site_target_to_cue_angles,
    target_az_from_mount_deg,
    validate_site_binding,
)
from monitor_core.turret.client import TurretClient

logger = logging.getLogger(__name__)


class TurretOrchestrator:
    """Один модуль турели: bind, фильтр цели, forward track."""

    def __init__(
        self,
        config: TurretConfig,
        client: TurretClient,
        *,
        site_name: str,
    ) -> None:
        self.config = config
        self.client = client
        self.site_name = site_name
        self._last_forward_ms: dict[str, int] = {}
        self._binding_ok = False
        self._binding_error: str | None = None

    @property
    def binding_ok(self) -> bool:
        return self._binding_ok

    @property
    def binding_error(self) -> str | None:
        return self._binding_error

    async def bind_to_site(self, site: SiteConfig) -> bool:
        if not self.config.enabled:
            self._binding_ok = True
            return True

        ok, msg = validate_site_binding(site, self.config)
        if not ok and self.config.site_binding.required:
            self._binding_ok = False
            self._binding_error = msg
            logger.error("turret %s binding failed: %s", self.config.id, msg)
            return False

        if not ok:
            logger.warning("turret %s binding soft mismatch: %s", self.config.id, msg)

        cmd = build_bind_command(site, self.config)
        bound = await self.client.bind(cmd)
        self._binding_ok = bound
        self._binding_error = None if bound else "bind rejected by turret controller"
        if bound and not is_calibration_complete(self.config.aim_calibration):
            logger.warning("turret %s: aim_calibration not finalized", self.config.id)
        return bound

    def slant_range_m(self, target: GeolocatedTarget) -> float:
        return distance_from_mount_m(
            target.position_enu_m,
            self.config.site_binding.offset_enu_m,
        )

    def should_forward(self, target: GeolocatedTarget) -> bool:
        if not self.config.enabled:
            return False
        if self.config.site_binding.required and not self._binding_ok:
            return False
        if target.class_name not in self.config.allowed_classes:
            return False
        if target.confidence < self.config.min_confidence:
            return False

        dist = self.slant_range_m(target)
        if dist > self.config.max_range_m or dist < self.config.min_range_m:
            return False

        az = target_az_from_mount_deg(
            target.position_enu_m,
            self.config.site_binding.offset_enu_m,
        )
        if not az_in_sector(az, self.config.sector_az_min_deg, self.config.sector_az_max_deg):
            return False

        return True

    async def forward_track(self, target: GeolocatedTarget, *, valid_ms: int = 500) -> bool:
        if not self.should_forward(target):
            return False

        now_ms = int(time.time() * 1000)
        min_interval_ms = int(1000 / self.config.track_forward_hz)
        last = self._last_forward_ms.get(target.target_id, 0)
        if now_ms - last < min_interval_ms:
            return False

        cue_az, cue_el = site_target_to_cue_angles(
            target.position_enu_m,
            self.config.site_binding,
            self.config.aim_calibration,
        )
        vel = target.velocity_enu_m_s or [0.0, 0.0, 0.0]
        cmd = TurretTrackCommand(
            target_id=target.target_id,
            site_id=self.config.site_binding.site_id,
            frame="site_enu",
            class_name=target.class_name,
            confidence=target.confidence,
            position_enu_m=target.position_enu_m,
            velocity_enu_m_s=vel,
            valid_until_ms=now_ms + valid_ms,
            cue_az_deg=cue_az,
            cue_el_deg=cue_el,
        )
        ok = await self.client.track(cmd)
        if ok:
            self._last_forward_ms[target.target_id] = now_ms
            logger.debug(
                "turret %s track %s dist=%.1fm",
                self.config.id,
                target.target_id,
                self.slant_range_m(target),
            )
        return ok

    async def safe_all(self, reason: str = "core_shutdown") -> None:
        if self.config.enabled:
            from monitor_core.models import TurretSafeCommand

            await self.client.safe(TurretSafeCommand(reason=reason))

    async def reachable(self) -> bool:
        return await self.client.reachable()
