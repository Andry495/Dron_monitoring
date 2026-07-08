from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class ScenarioKind(StrEnum):
    DRONE_APPROACH = "drone_approach"
    MULTI_ORBIT = "multi_orbit"
    CUSTOM = "custom"


@dataclass
class SimObject:
    id: str
    class_name: str
    confidence: float
    position_enu_m: list[float]
    velocity_enu_m_s: list[float]
    trail: list[list[float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "class": self.class_name,
            "confidence": self.confidence,
            "position_enu_m": self.position_enu_m,
            "velocity_enu_m_s": self.velocity_enu_m_s,
            "trail": self.trail[-120:],
        }


class ScenarioEngine:
    """Generates moving targets in site ENU for visualization and core feed."""

    def __init__(self) -> None:
        self.running = False
        self.kind = ScenarioKind.DRONE_APPROACH
        self.started_at = 0.0
        self.objects: list[SimObject] = []
        self._sky_cameras = ["sky_north", "sky_east", "sky_south", "sky_west"]

    def start(self, kind: ScenarioKind = ScenarioKind.DRONE_APPROACH) -> None:
        self.kind = kind
        self.running = True
        self.started_at = time.time()
        self.objects = self._spawn(kind)

    def stop(self) -> None:
        self.running = False
        self.objects = []

    def _spawn(self, kind: ScenarioKind) -> list[SimObject]:
        if kind == ScenarioKind.MULTI_ORBIT:
            return [
                SimObject(
                    id=f"sim-{uuid.uuid4().hex[:6]}",
                    class_name="drone",
                    confidence=0.92,
                    position_enu_m=[25.0, 0.0, 18.0],
                    velocity_enu_m_s=[0.0, 0.0, 0.0],
                ),
                SimObject(
                    id=f"sim-{uuid.uuid4().hex[:6]}",
                    class_name="plane",
                    confidence=0.88,
                    position_enu_m=[-40.0, 30.0, 80.0],
                    velocity_enu_m_s=[2.0, -1.0, 0.0],
                ),
            ]
        return [
            SimObject(
                id="sim-drone-1",
                class_name="drone",
                confidence=0.94,
                position_enu_m=[80.0, 20.0, 25.0],
                velocity_enu_m_s=[-4.5, -0.8, 0.2],
            )
        ]

    def tick(self, dt_s: float) -> None:
        if not self.running:
            return
        t = time.time() - self.started_at
        for obj in self.objects:
            if self.kind == ScenarioKind.MULTI_ORBIT and obj.class_name == "drone":
                r, h, w = 30.0, 20.0, 0.12
                obj.position_enu_m = [
                    r * math.cos(w * t),
                    r * math.sin(w * t),
                    h + 2 * math.sin(w * t * 0.5),
                ]
                obj.velocity_enu_m_s = [
                    -r * w * math.sin(w * t),
                    r * w * math.cos(w * t),
                    math.cos(w * t * 0.5),
                ]
            else:
                obj.position_enu_m = [
                    obj.position_enu_m[0] + obj.velocity_enu_m_s[0] * dt_s,
                    obj.position_enu_m[1] + obj.velocity_enu_m_s[1] * dt_s,
                    obj.position_enu_m[2] + obj.velocity_enu_m_s[2] * dt_s,
                ]
            obj.trail.append(list(obj.position_enu_m))

    def sky_detections(self) -> dict:
        """Synthetic sky detections for monitor-core sim feed."""
        out: dict = {}
        now = datetime.now(timezone.utc)
        for cam_id in self._sky_cameras:
            detections = []
            for obj in self.objects:
                az = math.degrees(math.atan2(obj.position_enu_m[0], obj.position_enu_m[1])) % 360
                el = math.degrees(
                    math.atan2(
                        obj.position_enu_m[2],
                        math.hypot(obj.position_enu_m[0], obj.position_enu_m[1]),
                    )
                )
                detections.append(
                    {
                        "class": obj.class_name,
                        "confidence": obj.confidence,
                        "bbox": {"x": 0.4, "y": 0.4, "w": 0.08, "h": 0.06},
                        "az_deg": az,
                        "el_deg": el,
                    }
                )
            out[cam_id] = {
                "camera_id": cam_id,
                "timestamp": now.isoformat(),
                "detections": detections,
            }
        return out

    def snapshot(self) -> dict:
        return {
            "running": self.running,
            "scenario": self.kind.value,
            "objects": [o.to_dict() for o in self.objects],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
