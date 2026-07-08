# Комплект камер v1 — BOM

Дата: 2026-07-08  
Статус: **утверждённый рекомендуемый вариант**

---

## Сводка

| Слой | Модель | Qty | Цена (ориентир) |
|------|--------|-----|-----------------|
| **Небо** | Hikvision DS-2CD2T47G2-L(2.8mm) | 4 | **32–56k ₽** |
| **Углы** | Hikvision DS-2DE4A425IWG-E | 4 | **168–232k ₽** |
| **Итого камеры** | | **8** | **~252k ₽** |

> **Камеры:** [camera-comparison.md](camera-comparison.md)  
> **ПК / switch / ai-engine:** [infrastructure-comparison.md](infrastructure-comparison.md)  
> **Мёртвые зоны:** [dead-zones.md](dead-zones.md)

Дополнительно: switch ~6.5k ₽, мини-ПК ~50k ₽, кабель, кронштейны V-slot, БП 12 V.

### Инфраструктура (не камеры)

| Позиция | Спецификация | Qty |
|---------|--------------|-----|
| Switch | 12p Gigabit, без PoE | 1 | TP-Link TL-SG1016D ~6.5k |
| мини-ПК | i5-12600H, 16 GB, SSD 512 GB | 1 | ~50k, CPU ai-engine |
| БП 12 V | 10–15 A, разводка на камеры | 1 |
| Кабель | Cat5e/Cat6 outdoor | 8 |
| Кронштейны | V-slot / 3D-печать | 8 |
| Куб / рама | V-slot 20×20, ~1 m³ | 1 |

---

## 1. Небо — 4× фиксированные (Sky)

### Hikvision DS-2CD2T47G2-L(2.8mm)

| Параметр | Значение |
|----------|----------|
| Тип | Bullet outdoor, **фикс** 2.8 mm |
| Разрешение | 4 MP (2688×1520) |
| HFOV | ~105° |
| Улица | IP67, ColorVu (день) |
| ONVIF / RTSP | Да |
| Субпоток | 720p для ai-engine |
| Цена | **8–14k ₽** / шт |

### Монтаж

- Позиция: **середина** каждой стороны верхней грани куба (N, E, S, W).
- Ось **вверх**, наклон **15–35°** к своему сектору.
- **Overlap** с соседними sky: **15–25%** HFOV.

### Альтернатива (не v1)

Dahua IPC-HFW2431S-S-S2(2.8mm) — дешевле, матрица 1/3".  
Hikvision DS-2CD2T86G2-4I(2.8mm) — 8 MP, +15–25% дальность motion.  
См. [camera-comparison.md](camera-comparison.md).

---

## 2. Углы — 4× готовая PTZ

### Hikvision DS-2DE4A425IWG-E

| Параметр | Значение |
|----------|----------|
| Разрешение | 4 MP (2560×1440) |
| Optical zoom | **25×** (4.8–120 mm) |
| HFOV | 53.3° … 2.6° |
| Pan / Tilt | 360° / −5°…90° |
| Улица | IP66 |
| ONVIF | Profile S, PTZ status |
| Питание | 12 V DC, ~24 W |
| Цена | **42–58k ₽** / шт |

### Монтаж

- Позиция: **углы** верхней грани куба (NW, NE, SE, SW).
- Home: ось **▲ вверх** (зенит).
- Базовый сектор привязан к N/E/S/W через калибровку.

### Управление (v1)

- **ONVIF:** `AbsoluteMove`, `GetStatus` (pan, tilt, zoom).
- Зум только **оптический** для геометрии.
- **ESP32 не используется.**

### Альтернатива

| Модель | Zoom | Цена / шт | Когда |
|--------|------|-----------|--------|
| Dahua DH-SD49425XB-HNR | 25× | 33–51k ₽ | Дешевле при закупке, STARVIS |
| Hikvision DS-2DE7A432IW-AEB(T5) | **32×** | 42–93k ₽ | Нужна дальность classify >700 m |

Подробно: [camera-comparison.md](camera-comparison.md).

---

## 3. Сеть

| IP | Устройство | Порт switch |
|----|------------|-------------|
| 192.168.10.10 | мини-ПК | 1 |
| .11 – .14 | Sky N, E, S, W | 2–5 |
| .21 – .24 | PTZ NE, SE, SW, NW | 6–9 |
| — | резерв / uplink | 10–12 |

**9 портов** занято. Wi‑Fi отключить в настройках камер.

---

## 4. Чеклист закупки

### Этап 1 — стенд (до 4 шт.)

- [ ] 1× DS-2DE4A425IWG-E — проверка ONVIF, RTSP 24 ч, зум-таблица
- [ ] 1× DS-2CD2T47G2-L — overlap с макетом куба
- [ ] мини-ПК или VM — ingest + ai-engine заглушка

### Этап 2 — комплект

- [ ] Sky × 4 (одинаковая партия)
- [ ] PTZ × 4
- [ ] Switch 12p
- [ ] Кронштейны / печать V-slot

---

## 5. Отложенные варианты

См. [alternatives.md](alternatives.md):

- 1× fisheye вместо 4 sky
- DIY bullet + ESP32 + шаговики
- MQTT / mosquitto

---

## Ссылки

- [Hikvision DS-2DE4A425IWG-E](https://us-legacy.hikvision.com/en/products/cameras/network-ptz-camera/value-series/ir/outdoor/4-mp-25-x-network-ir-ptz-camera-smart)
- [optics-and-range.md](optics-and-range.md)
