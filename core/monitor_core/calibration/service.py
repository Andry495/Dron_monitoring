from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from monitor_core.models import SiteConfig

logger = logging.getLogger(__name__)

CALIB_DIR = Path("data/calibration")


class CalibrationService:
    """Automated calibration wizard — dry-run friendly, writes reports to data/calibration/."""

    SCOPES = ("sky_overlap", "ptz_zoom", "site_origin", "turret_boresight")

    def __init__(self, site: SiteConfig) -> None:
        self.site = site
        self._jobs: dict[str, dict[str, Any]] = {}

    def start(self, scope: str) -> dict[str, Any]:
        if scope not in self.SCOPES:
            return {"ok": False, "error": f"unknown scope: {scope}"}
        job_id = f"cal-{scope}-{int(datetime.now(timezone.utc).timestamp())}"
        steps = self._steps_for(scope)
        job = {
            "id": job_id,
            "scope": scope,
            "status": "running",
            "steps": steps,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "recommendations": {},
        }
        self._jobs[job_id] = job
        asyncio.create_task(self._run_job(job_id))
        return {"ok": True, "job_id": job_id, **job}

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        return list(self._jobs.values())

    async def _run_job(self, job_id: str) -> None:
        job = self._jobs[job_id]
        scope = job["scope"]
        for step in job["steps"]:
            step["status"] = "running"
            await asyncio.sleep(0.8)
            step["status"] = "done"
            if step["id"] == "fit_sector" and scope == "sky_overlap":
                job["recommendations"]["sector_az_deg"] = "align to neighbor overlap ±2°"
            if step["id"] == "curve" and scope == "ptz_zoom":
                job["recommendations"]["zoom_curve"] = [
                    {"zoom": 0.0, "hfov_deg": 60},
                    {"zoom": 0.5, "hfov_deg": 20},
                    {"zoom": 1.0, "hfov_deg": 6},
                ]
            if step["id"] == "enu" and scope == "site_origin":
                job["recommendations"]["cameras"] = [
                    {"id": c.id, "offset_en_m": c.offset_en_m or [0, 0, 0]}
                    for c in self.site.cameras
                ]
            if step["id"] == "bore" and scope == "turret_boresight":
                job["recommendations"]["bore_offset_az_deg"] = 0.35
                job["recommendations"]["bore_offset_el_deg"] = -0.12

        job["status"] = "done"
        job["finished_at"] = datetime.now(timezone.utc).isoformat()
        self._persist(job)

    def _persist(self, job: dict[str, Any]) -> None:
        CALIB_DIR.mkdir(parents=True, exist_ok=True)
        path = CALIB_DIR / f"{job['id']}.json"
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Calibration report saved: %s", path)

    def _steps_for(self, scope: str) -> list[dict[str, Any]]:
        catalog = {
            "sky_overlap": [
                {"id": "capture", "title": "Снимок overlap с соседней sky", "auto": True, "status": "pending"},
                {"id": "fit_sector", "title": "Подбор sector_az_deg / mount_tilt_deg", "auto": True, "status": "pending"},
                {"id": "write", "title": "Запись в site.yaml", "auto": True, "status": "pending"},
            ],
            "ptz_zoom": [
                {"id": "goto_mark", "title": "ONVIF goto на калибровочную метку", "auto": True, "status": "pending"},
                {"id": "zoom_sweep", "title": "Съёмка HFOV по zoom", "auto": True, "status": "pending"},
                {"id": "curve", "title": "Построение zoom_curve", "auto": True, "status": "pending"},
            ],
            "site_origin": [
                {"id": "gps", "title": "GPS центра + углов здания", "auto": False, "status": "pending"},
                {"id": "enu", "title": "Расчёт offset_en_m камер", "auto": True, "status": "pending"},
            ],
            "turret_boresight": [
                {"id": "cue", "title": "Наведение на мишень", "auto": True, "status": "pending"},
                {"id": "bore", "title": "Измерение bore_offset", "auto": True, "status": "pending"},
            ],
        }
        return [dict(s) for s in catalog[scope]]
