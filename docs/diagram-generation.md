# Генерация иллюстраций для документации

**Единственный допустимый способ** создания PNG для `docs/images/` в этом проекте.

## Запрещено

| Метод | Почему |
|-------|--------|
| Плоские SVG → `resvg` PNG | Кириллица ломается на GitHub (`?????`), визуально «схема», не презентация |
| Текст кириллицей внутри AI-промпта | Нестабильный рендер шрифта |
| Ручное редактирование PNG без `_base` | Нет воспроизводимости |
| Вставка чужих картинок без `_base` в репозитории | Потеря pipeline |

Скрипты `scripts/deprecated/write-svgs.mjs` и `svg2png.mjs` **не использовать** для документации.

## Разрешённый pipeline (2 шага)

```text
1. AI-рендер базы (без текста)  →  docs/images/_base/*-base.png
2. Pillow + Arial               →  docs/images/*.png
```

### Шаг 1 — база (`_base/`)

- **Стиль:** фотореалистичный / изометрический 3D, тёмный tech-фон, presentation quality.
- **Промпт:** описание сцены на английском, в конце обязательно: `NO text, NO letters, NO labels`.
- **Инструмент:** Cursor `GenerateImage` (или тот же класс генератора).
- **Имя файла:** `{diagram-id}-base.png` (например `system-overview-base.png`).
- **Референс:** при обновлении можно передать `reference_image_paths` с предыдущей `_base` или оригиналом из git.

### Шаг 2 — подписи (кириллица)

- **Скрипт:** `scripts/compose-diagrams.py`
- **Шрифт:** `%WINDIR%\Fonts\arial.ttf` + `arialbd.ttf` (системный, не коммитится).
- **Выход:** `docs/images/{diagram-id}.png`

Пересборка всех зарегистрированных диаграмм:

```bash
pip install pillow
npm run images
# или: python scripts/compose-diagrams.py
```

## Реестр диаграмм

| ID | Выход PNG | База `_base/` | Где используется |
|----|-----------|---------------|------------------|
| `system-overview` | `system-overview.png` | `system-overview-base.png` | README hero |
| `detection-flow` | `detection-flow.png` | `detection-flow-base.png` | README, architecture |
| `network-topology` | `network-topology.png` | `network-topology-base.png` | README |
| `cube-top-view` | `cube-top-view.png` | `cube-top-base.png` | README, architecture |
| `cube-side-view` | `cube-side-view.png` | `cube-side-base.png` | README, architecture |
| `building-top-view` | `building-top-view.png` | `building-top-base.png` | README, deployment-building |

Новая диаграмма:

1. Добавить `{id}-base.png` в `docs/images/_base/`.
2. Добавить функцию `compose_{id}()` в `scripts/compose-diagrams.py` и вызов в `__main__`.
3. Обновить таблицу выше.
4. Закоммитить **и** `_base/`, **и** финальный PNG.

## Чеклист перед коммитом

- [ ] На PNG читается кириллица (открыть локально и на GitHub raw)
- [ ] База лежит в `_base/` и закоммичена
- [ ] `npm run images` воспроизводит тот же результат
- [ ] SVG из deprecated-папки не подключены в README/docs

## Структура файлов

```text
docs/images/
├── _base/                    # AI-рендер, без текста (источник истины для картинки)
│   └── system-overview-base.png
├── system-overview.png       # финал для README/docs
└── …

scripts/
├── compose-diagrams.py       # единственный активный генератор PNG
└── deprecated/               # старый SVG pipeline — не использовать
```
