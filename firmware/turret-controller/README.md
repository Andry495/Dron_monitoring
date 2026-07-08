# turret-controller — прошивка / логика реального времени

**Статус:** проект (модуль перехвата, не v1 наблюдения).

## Назначение

- Pan/tilt привод (шаговики + AS5600 или сервопривод).
- Контур TRACK 30–50 Hz.
- Пневмоклапан, датчик давления.
- Конечный автомат: SAFE → … → FIRE → COOLDOWN.
- Ethernet: приём трека от monitor-core, телеметрия.

## Не путать с

`firmware/ptz-controller/` — заготовка DIY для PTZ **куба** (не v1).

## Документация

- [docs/turret.md](../../docs/turret.md)
- [docs/turret-ballistics.md](../../docs/turret-ballistics.md)
- [config/turret.example.yaml](../../config/turret.example.yaml)

## Стек (план)

| Слой | Технология |
|------|------------|
| MCU | STM32H743 / ESP32-S3 |
| Привод | TMC2209 + NEMA23 pan, NEMA17 tilt |
| Сеть | LWIP / UDP + JSON |
| Камера | RTSP на agent или MJPEG на MCU |

## Сборка

```text
firmware/turret-controller/
├── src/
│   ├── main.c
│   ├── fsm.c           # состояния SAFE…FIRE
│   ├── pid_pan_tilt.c
│   ├── ballistics.c    # t_go, упреждение
│   ├── pneumatic.c
│   └── net_proto.c     # track от core
└── platformio.ini
```

Заглушка — до начала этапа 1 полигона.
