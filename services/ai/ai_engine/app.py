from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field


class DetectRequest(BaseModel):
    camera_id: str
    width: int = 1280
    height: int = 720
    image_b64: str | None = None


class DetectionBBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class DetectionOut(BaseModel):
    class_name: str = Field(alias="class")
    confidence: float
    bbox: DetectionBBox

    model_config = {"populate_by_name": True}


class DetectResponse(BaseModel):
    camera_id: str
    timestamp: str
    detections: list[DetectionOut] = Field(default_factory=list)


class ClassifyRequest(BaseModel):
    camera_id: str
    crop_b64: str | None = None


class ClassifyResponse(BaseModel):
    class_name: str = Field(alias="class")
    confidence: float

    model_config = {"populate_by_name": True}


def create_app() -> FastAPI:
    app = FastAPI(title="Dron Monitoring — ai-engine", version="0.1.0")

    @app.get("/v1/health")
    async def health():
        return {"status": "ok", "models_loaded": False}

    @app.post("/v1/detect", response_model=DetectResponse)
    async def detect(req: DetectRequest):
        # Stub: empty detections until ONNX models are wired
        return DetectResponse(
            camera_id=req.camera_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            detections=[],
        )

    @app.post("/v1/classify", response_model=ClassifyResponse)
    async def classify(req: ClassifyRequest):
        return ClassifyResponse(class_name="unknown", confidence=0.0)

    return app
