# monitor-core — v1
# ingest, sky_watch, tracker, onvif orchestrator, geolocate, api, recorder

См. [docs/architecture.md](../docs/architecture.md)

## Модули

| Модуль | Роль |
|--------|------|
| `ingest` | RTSP 4× sky + 4× PTZ |
| `sky_watch` | 4 потока, overlap merge |
| `tracker` | az/el, ByteTrack + Kalman |
| `orchestrator` | выбор 2 PTZ, ONVIF |
| `onvif_client` | pan/tilt/zoom, GetStatus |
| `geolocate` | триангуляция |
| `recorder` | клипы по событиям |
| `api` | REST / WebSocket |
| `turret_orchestrator` | опц.: трек → турель `.30` |

NN **не** в core — только HTTP к `ai-engine`.
