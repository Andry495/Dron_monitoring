# monitor-core

Ядро комплекса: ingest неба, ONVIF PTZ, трекинг, геолокация, оркестрация турели.

## Структура

```
core/
  monitor_core/
    api/              # FastAPI — статус, треки, PTZ, прокси турели
    config.py         # site.yaml + turret.yaml
    models.py         # Pydantic-модели
    ingest/           # RTSP (заглушка → OpenCV позже)
    onvif/            # ONVIF AbsoluteMove, GetStatus
    ai/               # HTTP-клиент ai-engine
    sky_watch/        # опрос 4× sky @ 2 FPS
    tracker/          # слияние детекций → az/el
    orchestrator/     # выбор 2 PTZ, cue
    geolocate/        # триангуляция 2 лучей → ENU
    turret/           # HTTP → turret-controller
    pipeline/         # coordinator — главный цикл
```

## Запуск (локально)

```bash
cp config/site.example.yaml config/site.yaml
cp config/turret.example.yaml config/turret.yaml
cp config/.env.example .env

cd core && pip install -e .
monitor-core
```

`DRY_RUN=true` — без реальных RTSP/ONVIF (для разработки на ПК).

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | liveness |
| GET | `/v1/status` | pipeline, камеры, турель |
| GET | `/v1/tracks` | активные треки (az/el) |
| GET | `/v1/targets` | геолокализованные цели |
| POST | `/v1/ptz/{id}/goto` | ручной cue PTZ |
| POST | `/v1/turrets/{id}/arm` | ARM одной турели |
| POST | `/v1/turret/safe` | SAFE на всех |
| GET | `/v1/turrets` | список модулей |

## Docker

```bash
docker compose up -d monitor-core ai-engine
docker compose --profile sim up -d   # + turret-sim на :8030
```

См. [docs/software-architecture.md](../docs/software-architecture.md).
