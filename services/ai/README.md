# ai-engine — v1

Отдельный сервис нейросети.

## API

| Method | Path | Назначение |
|--------|------|------------|
| POST | `/v1/detect` | 4× sky, движение / bbox |
| POST | `/v1/classify` | кроп PTZ → класс |
| GET | `/v1/health` | healthcheck |

## Модели

- `models/detect.onnx` — лёгкий детектор, INT8
- `models/classify.onnx` — drone / plane / helicopter / rocket / unknown

## Железо

| Режим | Runtime | Минимум | Рекомендуется v1 |
|-------|---------|---------|------------------|
| **CPU** (старт) | ONNX CPU EP, INT8 | 4C/8T, 16 GB RAM | **i5-12600H**, 16 GB, 4×720p @ 2 FPS |
| **GPU** (апгрейд) | ONNX CUDA / TensorRT | GTX 1650 4 GB | **RTX 4060 8 GB**, 4×10+ FPS |

Подробные таблицы, Docker-лимиты и пороги «когда нужен GPU»:  
[infrastructure-comparison.md](../docs/infrastructure-comparison.md) §4

См. также [architecture.md](../docs/architecture.md) §5
