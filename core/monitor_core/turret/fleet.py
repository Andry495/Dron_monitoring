from __future__ import annotations

import logging

from monitor_core.models import GeolocatedTarget, SiteConfig, TurretArmCommand, TurretSafeCommand
from monitor_core.turret.orchestrator import TurretOrchestrator

logger = logging.getLogger(__name__)


class TurretFleetOrchestrator:
    """
    Несколько турелей на одной площадке.
    На каждую цель — одна «лучшая» турель (в зоне, ближайшая к цели, выше priority).
    """

    def __init__(self, units: list[TurretOrchestrator]) -> None:
        self.units = units
        self._assignment: dict[str, str] = {}

    @property
    def enabled_units(self) -> list[TurretOrchestrator]:
        return [u for u in self.units if u.config.enabled]

    def get(self, turret_id: str) -> TurretOrchestrator | None:
        for unit in self.units:
            if unit.config.id == turret_id:
                return unit
        return None

    async def bind_all(self, site: SiteConfig) -> None:
        for unit in self.units:
            if unit.config.enabled:
                await unit.bind_to_site(site)

    def select_for_target(self, target: GeolocatedTarget) -> TurretOrchestrator | None:
        sticky_id = self._assignment.get(target.target_id)
        if sticky_id:
            sticky = self.get(sticky_id)
            if sticky and sticky.should_forward(target):
                return sticky

        candidates = [u for u in self.enabled_units if u.should_forward(target)]
        if not candidates:
            self._assignment.pop(target.target_id, None)
            return None

        best = min(
            candidates,
            key=lambda u: (
                u.slant_range_m(target),
                -u.config.priority,
                u.config.id,
            ),
        )
        self._assignment[target.target_id] = best.config.id
        return best

    async def forward_track(self, target: GeolocatedTarget) -> bool:
        unit = self.select_for_target(target)
        if unit is None:
            return False
        return await unit.forward_track(target)

    async def safe_all(self, reason: str = "core_shutdown") -> None:
        for unit in self.enabled_units:
            await unit.safe_all(reason)

    async def arm(self, turret_id: str | None, cmd: TurretArmCommand) -> bool:
        if turret_id:
            unit = self.get(turret_id)
            return await unit.client.arm(cmd) if unit else False
        ok = False
        for unit in self.enabled_units:
            ok = await unit.client.arm(cmd) or ok
        return ok

    async def safe(self, turret_id: str | None, cmd: TurretSafeCommand) -> bool:
        if turret_id:
            unit = self.get(turret_id)
            return await unit.client.safe(cmd) if unit else False
        ok = False
        for unit in self.enabled_units:
            ok = await unit.client.safe(cmd) or ok
        return ok

    async def close_all(self) -> None:
        seen: set[str] = set()
        for unit in self.units:
            url = unit.client.base_url
            if url not in seen:
                await unit.client.close()
                seen.add(url)
