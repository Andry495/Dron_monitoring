from __future__ import annotations

import logging
from pathlib import Path

from monitor_core.config import load_turret_yaml
from monitor_core.models import SiteConfig, TurretConfig
from monitor_core.turret.client import TurretClient
from monitor_core.turret.fleet import TurretFleetOrchestrator
from monitor_core.turret.orchestrator import TurretOrchestrator

logger = logging.getLogger(__name__)


def load_turret_configs(site: SiteConfig, fallback_path: Path | None) -> list[TurretConfig]:
    """Список турелей: из site.bound_turrets, иначе один файл config/turret.yaml."""
    configs: list[TurretConfig] = []
    base_dir = Path(".")

    for ref in site.bound_turrets:
        if not ref.enabled:
            continue
        path = Path(ref.config)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            if ref.optional:
                logger.warning("turret config missing (optional): %s", path)
                continue
            raise FileNotFoundError(f"turret config not found: {path}")
        cfg = load_turret_yaml(path)
        if ref.id:
            cfg.id = ref.id
        configs.append(cfg)

    if not configs and fallback_path and fallback_path.exists():
        configs.append(load_turret_yaml(fallback_path))

    return configs


def build_turret_fleet(site: SiteConfig, fallback_path: Path | None) -> TurretFleetOrchestrator:
    configs = load_turret_configs(site, fallback_path)
    units: list[TurretOrchestrator] = []
    for cfg in configs:
        client = TurretClient(cfg.controller_url)
        units.append(
            TurretOrchestrator(cfg, client, site_name=site.name),
        )
    logger.info("Turret fleet: %d module(s), %d enabled", len(units), sum(1 for c in configs if c.enabled))
    return TurretFleetOrchestrator(units)
