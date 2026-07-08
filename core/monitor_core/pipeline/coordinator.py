from __future__ import annotations

import asyncio
import logging

import httpx

from monitor_core.ai.client import AiEngineClient
from monitor_core.calibration.service import CalibrationService
from monitor_core.config import Settings
from monitor_core.geolocate.triangulation import GeolocateService
from monitor_core.models import GeolocatedTarget, SystemStatus, TrackState, TurretUnitStatus
from monitor_core.onvif.client import PtzPool
from monitor_core.operation_mode import OperationMode
from monitor_core.orchestrator.ptz import PtzOrchestrator
from monitor_core.sim.feed import SimFeedService
from monitor_core.sky_watch.service import SkyWatchService
from monitor_core.tracker.service import TrackerService
from monitor_core.turret.registry import build_turret_fleet

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Wires sky_watch → tracker → PTZ orchestrator → geolocate → turret fleet."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.site = settings.load_site()
        self.operation_mode = OperationMode(settings.pipeline_mode)

        sky = self.site.sky_cameras()
        ptz = self.site.ptz_cameras()
        cam_map = {c.id: c for c in self.site.cameras}

        self.ai = AiEngineClient(settings.ai_engine_url)
        self.sky_watch = SkyWatchService(
            sky,
            self.ai,
            fps=settings.sky_detect_fps,
            dry_run=settings.dry_run,
        )
        self.sim_feed = SimFeedService(settings.simulator_url)
        self.tracker = TrackerService(cam_map)
        self.ptz_pool = PtzPool(
            ptz,
            settings.onvif_password_for("ptz"),
            dry_run=settings.dry_run,
        )
        self.ptz_orchestrator = PtzOrchestrator(ptz, self.ptz_pool)
        self.geolocate = GeolocateService(self.site)
        self.turret_fleet = build_turret_fleet(self.site, settings.turret_config)
        self.calibration = CalibrationService(self.site)

        self.geolocated_targets: list[GeolocatedTarget] = []
        self._sky_task: asyncio.Task | None = None
        self._pipeline_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self.ptz_pool.connect_all()
        await self.turret_fleet.bind_all(self.site)
        self._running = True
        if self.operation_mode == OperationMode.SIMULATION:
            await self.sim_feed.start()
        else:
            self._sky_task = asyncio.create_task(self.sky_watch.run(), name="sky_watch")
        self._pipeline_task = asyncio.create_task(self._pipeline_loop(), name="pipeline")
        logger.info(
            "Pipeline started (mode=%s, dry_run=%s)",
            self.operation_mode.value,
            self.settings.dry_run,
        )

    async def stop(self) -> None:
        self._running = False
        self.sky_watch.stop()
        await self.sim_feed.stop()
        await self.turret_fleet.safe_all("core_shutdown")
        for task in (self._sky_task, self._pipeline_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.ptz_pool.disconnect_all()
        await self.ai.close()
        await self.turret_fleet.close_all()
        logger.info("Pipeline stopped")

    async def set_mode(self, mode: OperationMode) -> None:
        if mode == self.operation_mode:
            return
        self.operation_mode = mode
        if mode == OperationMode.SIMULATION:
            self.sky_watch.stop()
            if self._sky_task:
                self._sky_task.cancel()
                self._sky_task = None
            await self.sim_feed.start()
        else:
            await self.sim_feed.stop()
            self._sky_task = asyncio.create_task(self.sky_watch.run(), name="sky_watch")
        logger.info("Operation mode → %s", mode.value)

    async def _pipeline_loop(self) -> None:
        interval = 1.0 / self.settings.pipeline_tick_hz
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("pipeline tick failed")
            await asyncio.sleep(interval)

    async def _tick(self) -> None:
        if self.operation_mode == OperationMode.SIMULATION:
            detections = self.sim_feed.latest_detections
        else:
            detections = self.sky_watch.latest_detections
        tracks = self.tracker.update(detections)
        if tracks:
            self.ptz_orchestrator.cue_tracks(tracks)
        self.geolocated_targets = self._geolocate_tracks(tracks)
        for target in self.geolocated_targets:
            await self.turret_fleet.forward_track(target)

    def _geolocate_tracks(self, tracks: list[TrackState]) -> list[GeolocatedTarget]:
        results: list[GeolocatedTarget] = []
        ptz_ids = self.ptz_pool.camera_ids
        if len(ptz_ids) < 2:
            return results

        for track in tracks[:2]:
            ray_a = (ptz_ids[0], track.az_deg, track.el_deg)
            ray_b = (ptz_ids[1], track.az_deg, track.el_deg)
            target = self.geolocate.triangulate(track, ray_a, ray_b)
            if target:
                results.append(target)
        return results

    def site_layout(self) -> dict:
        return {
            "name": self.site.name,
            "deployment_type": self.site.deployment_type,
            "origin": {
                "lat": self.site.origin_lat,
                "lon": self.site.origin_lon,
                "alt_m": self.site.origin_alt_m,
            },
            "cameras": [
                {
                    "id": c.id,
                    "role": c.role.value,
                    "offset_en_m": c.offset_en_m,
                    "corner": c.corner,
                    "mount_az_deg": c.mount_az_deg,
                }
                for c in self.site.cameras
            ],
            "turrets": [
                {
                    "id": u.config.id,
                    "enabled": u.config.enabled,
                    "offset_enu_m": u.config.site_binding.offset_enu_m,
                    "sector_az_deg": [u.config.sector_az_min_deg, u.config.sector_az_max_deg],
                }
                for u in self.turret_fleet.units
            ],
        }

    async def fetch_sim_objects(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.settings.simulator_url.rstrip('/')}/v1/scenario/state")
                resp.raise_for_status()
                return resp.json().get("objects", [])
        except Exception:
            return []

    async def system_status(self) -> SystemStatus:
        turret_rows: list[TurretUnitStatus] = []
        for unit in self.turret_fleet.units:
            reachable = None
            if unit.config.enabled:
                reachable = await unit.reachable()
            turret_rows.append(
                TurretUnitStatus(
                    id=unit.config.id,
                    enabled=unit.config.enabled,
                    controller_url=unit.config.controller_url,
                    binding_ok=unit.binding_ok,
                    binding_error=unit.binding_error,
                    reachable=reachable,
                    offset_enu_m=list(unit.config.site_binding.offset_enu_m),
                )
            )

        enabled = [r for r in turret_rows if r.enabled]
        first = enabled[0] if enabled else None
        return SystemStatus(
            pipeline_running=self._running,
            operation_mode=self.operation_mode.value,
            sky_cameras_online=len(self.site.sky_cameras()),
            ptz_cameras_online=len(self.ptz_pool.camera_ids),
            active_tracks=len(self.tracker.tracks),
            turret_enabled=bool(enabled),
            turret_count=len(turret_rows),
            turrets=turret_rows,
            turret_reachable=first.reachable if first else None,
            turret_binding_ok=first.binding_ok if first else None,
        )
