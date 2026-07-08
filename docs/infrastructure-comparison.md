# Сравнение: мини-ПК, коммутатор, ai-engine

Дата: 2026-07-08  
Контекст: один хост на площадке — **monitor-core** + **ai-engine** + recorder.

Цены — ориентир по KNS, TP-Link, Minisforum, Beelink и др. (РФ, 2025–2026).

---

## 0. Нагрузка системы (от чего считать железо)

### Сеть (коммутатор)

| Поток | Разрешение | Битрейт (ориентир) | Кто потребляет |
|-------|------------|-------------------|----------------|
| Sky ×4 субпоток | 720p H.265 | 1–2 Mbit/s каждый | core → ai-engine `/detect` |
| PTZ ×4 субпоток | 720p | 1–2 Mbit/s | core (наведение) |
| PTZ ×4 main (событие) | 1440p | 4–8 Mbit/s | recorder, `/classify` |

| Режим | Суммарный трафик LAN |
|-------|----------------------|
| Фон (только sky sub) | **4–8 Mbit/s** |
| Сопровождение (sub + 2 PTZ main) | **15–25 Mbit/s** |
| Пик (все 8 main/sub) | **50–120 Mbit/s** |

**Вывод:** достаточно **Gigabit**, 100 Mbit/s не нужен. PoE в v1 **не используется**.

### CPU / RAM (monitor-core)

| Задача | Нагрузка |
|--------|----------|
| RTSP ingest 8 потоков | 15–35% CPU (с **аппаратным** decode: QSV/VAAPI) |
| ONVIF, tracker, API | 5–15% |
| Recorder (по событию) | пики до 30% + диск |

**Рекомендация:** 4+ физических ядра; обязательно **аппаратное декодирование H.264/H.265** (Intel Quick Sync или AMD VCN).

### ai-engine (отдельно — см. §4)

| Режим | Нагрузка |
|-------|----------|
| CPU INT8, 4×720p @ 2 FPS | ~40–70% одного 6–8 ядерного CPU |
| GPU, тот же режим | ~5–15% RTX 3050/4060 |

---

## 1. Коммутатор — сравнительная таблица

Нужно: **≥12 портов RJ-45**, Gigabit, **без PoE**, 9 портов занято.

| Модель | Порты | Управление | PoE | Fanless | Цена | Оценка |
|--------|-------|------------|-----|---------|------|--------|
| **TP-Link TL-SG1016D** ⭐ | 16×1G | Нет | Нет | Да | **6 000 – 7 000 ₽** | **Рекомендуется v1** — дёшево, 16 портов, запас |
| D-Link DGS-1016D | 16×1G | Нет | Нет | Да | 5 100 – 5 600 ₽ | Аналог TP-Link |
| D-Link DGS-1100-16V2 | 16×1G | Web smart | Нет | Нет | 8 500 – 9 500 ₽ | VLAN, mirror — если нужна диагностика |
| D-Link DGS-1210-10 | 8×1G + 2 SFP | Web smart | Нет | Да | 7 300 – 8 100 ₽ | **Мало портов** (только 8 медь) |
| MikroTik CRS310-8G+2S+ | 8×1G + 2 SFP+ | RouterOS | Нет | Да | 15 000 – 22 000 ₽ | Мало портов, избыточен для v1 |
| D-Link DGS-1510-28P | 24×1G PoE | Smart | **Да** | Нет | 40 000+ ₽ | Не v1 (PoE не нужен) |

### Коммутатор — вывод

| Вариант | Когда |
|---------|--------|
| **TP-Link TL-SG1016D** | Стандарт v1: 16 портов, ~6.5k ₽ |
| DGS-1100-16V2 | Нужен VLAN 10 для камер / port mirror для отладки |
| DGS-1210-10 | **Не брать** — 8 медных портов мало |

---

## 2. Мини-ПК — сравнительная таблица (CPU-only, v1)

Один ПК: Docker **monitor-core** + **ai-engine (CPU)** + recorder.

| Модель / конфиг | CPU | Ядра | RAM | SSD | GPU decode | Цена | Оценка |
|-----------------|-----|------|-----|-----|------------|------|--------|
| Beelink Mini S (N100) | Intel N100 | 4C/4T | 16 GB | 500 GB | Quick Sync | 25 000 – 35 000 ₽ | **Минимум** — ai-engine на пределе |
| **Beelink SER5 5560U** | Ryzen 5 5560U | 6C/12T | 16 GB | 512 GB | VAAPI | **33 000 – 47 000 ₽** | **Бюджет v1** |
| Minisforum UN1245 | i5-12450H | 8C/12T | 16 GB | 512 GB | Quick Sync | 49 000 – 52 000 ₽ | Хороший баланс |
| **Minisforum NAB6 Lite** ⭐ | i5-12600H | 12C/16T | 16 GB | 512 GB | Quick Sync | **50 000 – 55 000 ₽** | **Рекомендуется v1** |
| Minisforum NAB6 32/1TB | i5-12600H | 12C/16T | **32 GB** | 1 TB | Quick Sync | 60 000 – 77 000 ₽ | Запас под архив + dev |
| Minisforum UM760 Slim | Ryzen 5 7640HS | 6C/12T | 16 GB | 512 GB | VAAPI | 55 000 – 65 000 ₽ | Альтернатива Intel |
| Dell OptiPlex Micro (б/у) | i5-12500T / i5-13500T | 6–14C | 16 GB | 512 GB | Quick Sync | 45 000 – 65 000 ₽ | Корп. гарантия, компактный |
| Lenovo ThinkCentre M70q Gen4 | i5-13500T | 14C | 16 GB | 512 GB | Quick Sync | 55 000 – 75 000 ₽ | Надёжность, дороже |

### Мини-ПК CPU-only — вывод

| Уровень | Конфиг | Цена | Комментарий |
|---------|--------|------|-------------|
| Минимум | N100 / 16 GB | ~30k | Только стенд; в бою возможны просадки `/detect` |
| **Рекомендуется** | **i5-12600H / 16 / 512** | **~50k** | 4× sky @ 2 FPS INT8 + ingest без GPU |
| Комфорт | i5-12600H / **32 / 1 TB** | ~70k | Архив событий, VM на том же железе нежелательно |

**ОС:** Linux (Ubuntu 22.04+ / Debian 12) + Docker. Windows с Hyper-V — только dev.

---

## 3. Мини-ПК — с GPU (ai-engine на видеокарте)

| Модель / конфиг | CPU | GPU | VRAM | RAM | Цена | Оценка |
|-----------------|-----|-----|------|-----|------|--------|
| Сборка SFF i5 + RTX 3050 | i5-12400 | RTX 3050 | 6 GB | 16 GB | 65 000 – 85 000 ₽ | Бюджет GPU |
| **Minisforum 795S7** | Ryzen 9 7945HX | **RTX 4060** | 8 GB | 32 GB | **70 000 – 120 000 ₽** | Компактный GPU-комплект |
| Thunderobot Mix | i7-13620H | RTX 4060 | 8 GB | 16 GB | ~190 000 ₽ | Импорт, переплата |
| **Jetson Orin NX 16GB** (dev kit) | 8×A78 | Ampere | shared 16 GB | 16 GB | **130 000 – 180 000 ₽** | Отдельный AI-бокс, другой стек (TensorRT) |

### GPU-ПК — вывод

| Вариант | Когда |
|---------|--------|
| Оставить CPU-only | v1 достаточно: 4×720p @ 1–2 FPS, INT8 |
| RTX 3050/4060 в том же ПК | Нужно 4×5 FPS detect, YOLO-medium, несколько PTZ `/classify` параллельно |
| Jetson Orin NX | Отдельный узел ai-engine, жёсткое энергопотребление, **не** смешивать с x86 без причины |

---

## 4. ai-engine — требования к железу

### 4.1 Профиль нагрузки v1

| Endpoint | Вход | Частота | Модель (ориентир) |
|----------|------|---------|-------------------|
| `POST /v1/detect` | 1280×720, 4 потока | **1–2 FPS** на поток | YOLO-nano / YOLOv8n INT8 |
| `POST /v1/classify` | 224×224 … 640×640 кроп | по событию, 1–5 / с | MobileNet / ResNet18 INT8 |

Суммарно: **4–8 инференсов detect/сек** + редкий classify.

### 4.2 Вариант A — CPU only (рекомендуется v1)

Runtime: **ONNX Runtime**, `CPUExecutionProvider`, модели **INT8**.

| Уровень | CPU | Системная RAM | RAM ai-engine¹ | SSD | Detect (4×720p) | Модели |
|---------|-----|---------------|----------------|-----|-----------------|--------|
| **Минимум** | 4C/8T, AVX2 (N100, i3) | 16 GB | 4 GB | 256 GB | 4×**1 FPS** | nano INT8 |
| **Рекомендуется** ⭐ | **6–8C/12T** (i5-12450H, R5 5560U, **i5-12600H**) | **16 GB** | **6 GB** | **512 GB** | 4×**2 FPS** | small INT8 |
| Запас | 8C+ (i7, R7), 12 потоков+ | **32 GB** | 8 GB | 1 TB | 4×**3–4 FPS** | small/medium INT8 |

¹ Лимит Docker `mem_limit` для контейнера `ai-engine`.

**Параметры ONNX Runtime (CPU):**

```yaml
# ориентир config/ai-engine.yaml
intra_op_num_threads: 4      # на 6–8 ядерном CPU
inter_op_num_threads: 2
execution_mode: parallel
graph_optimization_level: all
```

**Ожидаемая задержка** (YOLOv8n INT8, 720p, 1 поток):

| CPU | ms / кадр | 4 потока × 2 FPS |
|-----|-----------|------------------|
| N100 | 120–200 | на пределе |
| R5 5560U | 60–100 | ок |
| i5-12600H | 40–70 | комфортно |

### 4.3 Вариант B — с GPU

Runtime: ONNX Runtime **CUDAExecutionProvider** или **TensorRT**.

| Уровень | GPU | VRAM | Системная RAM | Detect (4×720p) | Classify | Модели |
|---------|-----|------|---------------|-----------------|----------|--------|
| **Минимум** | GTX 1650 / **Intel Arc A380** | 4–6 GB | 16 GB | 4×5 FPS | пакетно | small INT8 |
| **Рекомендуется** ⭐ | **RTX 3050 6GB / RTX 4060 8GB** | 6–8 GB | 16–32 GB | 4×**10–15 FPS** | без очереди | small + medium |
| Запас | RTX 4060 Ti 16GB | 16 GB | 32 GB | 4×25+ FPS | multi-crop | medium/large, FP16 |

**Когда GPU оправдан:**

| Условие | CPU | GPU |
|---------|-----|-----|
| Detect 1–2 FPS, INT8 nano/small | ✅ достаточно | избыточен |
| Detect **≥4 FPS** на все sky | ⚠️ на пределе | ✅ |
| Модель **YOLO-medium+** | ❌ | ✅ |
| Несколько `/classify` одновременно на 4 PTZ | ⚠️ | ✅ |
| Задержка detect **<100 ms** | ⚠️ | ✅ |

**Параметры Docker (GPU):**

```yaml
# docker-compose.yml — фрагмент
ai-engine:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  mem_limit: 4g   # системная RAM; VRAM — отдельно
```

```yaml
# ONNX Runtime
execution_providers:
  - CUDAExecutionProvider
  - CPUExecutionProvider
```

### 4.4 Сводка: CPU vs GPU для ai-engine

| | CPU only (v1) | + GPU |
|--|---------------|-------|
| **Железо** | i5-12600H, 16 GB | + RTX 4060 8 GB |
| **Доп. бюджет** | 0 | **+20 000 – 50 000 ₽** (или отдельный GPU-ПК) |
| **Потребление** | ~25–45 W CPU | +75–115 W GPU |
| **Detect** | 4×2 FPS INT8 | 4×10+ FPS |
| **Стек** | ONNX CPU INT8 | ONNX CUDA / TensorRT |
| **Сложность** | низкая | драйвер NVIDIA, nvidia-container-toolkit |
| **Рекомендация** | **старт v1** | при нехватке FPS или апгрейде модели |

---

## 5. Сводные комплекты «под ключ» (без камер)

| Комплект | Switch | ПК | ai-engine | Итого инфра | Комментарий |
|----------|--------|-----|-----------|-------------|-------------|
| **v1 бюджет** | TL-SG1016D ~6.5k | SER5 5560U ~40k | CPU | **~47k** | Стенд / пилот |
| **v1 рекомендуемый** ⭐ | TL-SG1016D ~6.5k | NAB6 i5-12600H ~50k | CPU | **~57k** | Бой на площадке |
| v1 + архив | TL-SG1016D | NAB6 32GB/1TB ~70k | CPU | **~77k** | Длинный архив клипов |
| v1 + GPU | TL-SG1016D | 795S7 RTX4060 ~90k | CUDA | **~97k** | 4×5+ FPS detect |
| v1 managed net | DGS-1100-16 ~9k | NAB6 ~50k | CPU | **~59k** | VLAN / mirror |

*Без БП 12 V, кабеля, ИБП, шкафа.*

---

## 6. Итоговая рекомендация

### Коммутатор
**TP-Link TL-SG1016D** (16× Gigabit, ~6 500 ₽) — вместо абстрактного «switch 12p ~5k».

### Мини-ПК (v1)
**Minisforum NAB6 Lite: i5-12600H / 16 GB / 512 GB SSD** (~50 000 ₽)  
или **Beelink SER5 5560U** (~40 000 ₽) при жёстком бюджете.

### ai-engine
- **Старт: CPU only**, ONNX INT8, 4×720p @ **2 FPS**.
- **GPU** — при переходе на 4+ FPS или модели medium+; минимум **RTX 3050 6 GB**, лучше **RTX 4060 8 GB**.

### ИБП (опционально)
ИБП 600–1000 VA (~5–12k ₽) на ПК + switch — 10–15 мин автономии при сбое 220 V.

---

## 7. Источники цен

| Позиция | Источник | Цена |
|---------|----------|------|
| TP-Link TL-SG1016D | [KNS](https://www.kns.ru/product/kommutator-tp-link-tl-sg1016d/) | от 6 562 ₽ |
| D-Link DGS-1100-16V2 | [KNS](https://www.kns.ru/catalog/setevoe-oborudovanie/kommutatory/d-link/_kolichestvo-portov_16/) | 8 588 ₽ |
| Minisforum NAB6 Lite | [Market777](https://www.market777.ru/product/mini-pk-minisforum-mini-nav6-lite-intel-core-i5-12600h-16-gb-ddr4-512-gb-ssd-intel-iris-xe-graphics/) | 50 370 ₽ |
| Minisforum UN1245 | [4pc.ru](https://www.4pc.ru/catalog/nastolnye-pk-i-monobloki/mini-pk-minisforum-un1245-16gb-512gb-i5-124-1530086141100) | 49 028 ₽ |
| Beelink SER5 | [bee-link.ru](https://bee-link.ru/ser5) | 46 800 ₽ |
| Jetson Orin NX 16GB | [AN-CHIP](https://an-chip.ru/nvidia-jetson-orin-nx-16gb/) | от 134 737 ₽ |

См. также: [architecture.md](architecture.md) · [camera-comparison.md](camera-comparison.md)
