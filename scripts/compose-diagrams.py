"""Compose photorealistic diagram bases + Cyrillic labels (Pillow)."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"
BASE = IMG / "_base"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    windir = os.environ.get("WINDIR", r"C:\Windows")
    path = Path(windir) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf")
    if not path.exists():
        path = Path(windir) / "Fonts" / "arial.ttf"
    return ImageFont.truetype(str(path), size)


def center_text(draw: ImageDraw.ImageDraw, y: int, text: str, w: int, fnt, fill: str) -> None:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, y), text, font=fnt, fill=fill)


def label_card(draw, x: int, y: int, w: int, title: str, sub: str, title_font, sub_font) -> None:
    cx = x + w // 2
    tb = draw.textbbox((0, 0), title, font=title_font)
    tw = tb[2] - tb[0]
    draw.text((cx - tw // 2, y), title, font=title_font, fill="#f8fafc")
    if sub:
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        sw = sb[2] - sb[0]
        draw.text((cx - sw // 2, y + 22), sub, font=sub_font, fill="#cbd5e1")


def compose_system_overview() -> None:
    src = BASE / "system-overview-base.png"
    if not src.exists():
        raise FileNotFoundError(src)
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title_f = font(42, bold=True)
    sub_f = font(22)
    zone_f = font(20, bold=True)
    card_t = font(18, bold=True)
    card_s = font(14)

    # Semi-transparent title bar
    draw.rectangle([0, 0, w, 100], fill=(15, 23, 42, 180))
    center_text(draw, 18, "Dron Monitoring — комплект v1", w, title_f, "#f8fafc")
    center_text(draw, 62, "4× Sky fixed + 4× PTZ 25× · mini-PC · ai-engine · operator-ui", w, sub_f, "#94a3b8")

    # Zone label on dome area
    zt = "зона обзора / видимости"
    zb = draw.textbbox((0, 0), zt, font=zone_f)
    ztw = zb[2] - zb[0]
    draw.text(((w - ztw) // 2, int(h * 0.12)), zt, font=zone_f, fill="#7dd3fc")

    # Bottom module cards (approx positions for 16:9)
    cards = [
        (int(w * 0.06), "mini-PC", "monitor-core"),
        (int(w * 0.24), "ai-engine", "детект · класс"),
        (int(w * 0.42), "operator-ui", "карта · калибр."),
        (int(w * 0.60), "simulator", "сценарии"),
        (int(w * 0.78), "Switch 12p", "8 камер + ПК"),
    ]
    card_w = int(w * 0.16)
    card_y = int(h * 0.88)
    for x, title, sub in cards:
        label_card(draw, x, card_y, card_w, title, sub, card_t, card_s)

    note = "без ESP32 · без MQTT · PTZ: ONVIF"
    nb = draw.textbbox((0, 0), note, font=card_s)
    draw.text((w - (nb[2] - nb[0]) - 24, 24), note, font=card_s, fill="#86efac")

    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "system-overview.png", quality=95)
    print("wrote system-overview.png")


def compose_detection_flow() -> None:
    src = BASE / "detection-flow-base.png"
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title_f = font(40, bold=True)
    step_f = font(16, bold=True)
    sub_f = font(13)

    draw.rectangle([0, 0, w, 90], fill=(15, 23, 42, 190))
    center_text(draw, 16, "Поток обработки v1", w, title_f, "#f8fafc")
    center_text(draw, 54, "live: RTSP sky · simulation: scenario-simulator", w, sub_f, "#94a3b8")

    steps = ["4× Sky", "/detect", "трек", "ONVIF", "zoom", "/classify", "гео", "UI/WS"]
    subs = ["RTSP", "ai-engine", "az/el", "PTZ", "main", "ai-engine", "2× PTZ", "оператор"]
    n = len(steps)
    xs = [int(w * (0.06 + i * 0.115)) for i in range(n)]
    y = int(h * 0.82)
    for x, st, sb in zip(xs, steps, subs):
        label_card(draw, x, y, int(w * 0.1), st, sb, step_f, sub_f)

    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "detection-flow.png", quality=95)
    print("wrote detection-flow.png")


def compose_network_topology() -> None:
    src = BASE / "network-topology-base.png"
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title_f = font(40, bold=True)
    sub_f = font(20)
    lbl_f = font(17, bold=True)
    small_f = font(14)

    draw.rectangle([0, 0, w, 95], fill=(15, 23, 42, 190))
    center_text(draw, 14, "Сеть v1 — 192.168.10.0/24", w, title_f, "#f8fafc")
    center_text(draw, 52, "Switch 12p без PoE · 9 портов занято", w, sub_f, "#94a3b8")

    items = [
        (int(w * 0.08), int(h * 0.35), "mini-PC .10", "core·ai·ui"),
        (int(w * 0.40), int(h * 0.42), "Switch 12p", "центр L2"),
        (int(w * 0.72), int(h * 0.22), "Sky .11–.14", "4× фикс"),
        (int(w * 0.72), int(h * 0.48), "PTZ .21–.24", "4× ONVIF"),
        (int(w * 0.72), int(h * 0.72), "turret .30+", "опц."),
    ]
    for x, y, t1, t2 in items:
        label_card(draw, x, y, int(w * 0.18), t1, t2, lbl_f, small_f)

    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "network-topology.png", quality=95)
    print("wrote network-topology.png")


def compose_cube_top() -> None:
    src = BASE / "cube-top-base.png"
    if not src.exists():
        return
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_f, sub_f, lbl_f = font(38, bold=True), font(20), font(16, bold=True)
    draw.rectangle([0, 0, w, 88], fill=(15, 23, 42, 190))
    center_text(draw, 12, "Вид сверху — cube_compact", w, title_f, "#f8fafc")
    center_text(draw, 50, "4× Sky (середины) + 4× PTZ (углы) · overlap 20%", w, sub_f, "#94a3b8")
    center_text(draw, int(h * 0.92), "N ▲", w, font(24, bold=True), "#38bdf8")
    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "cube-top-view.png", quality=95)
    print("wrote cube-top-view.png")


def compose_building_top() -> None:
    src = BASE / "building-top-base.png"
    if not src.exists():
        return
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_f, sub_f = font(38, bold=True), font(20)
    draw.rectangle([0, 0, w, 88], fill=(15, 23, 42, 190))
    center_text(draw, 12, "Вид сверху — building_corners", w, title_f, "#f8fafc")
    center_text(draw, 50, "4 угла Sky+PTZ · купол-hub по центру (ПК)", w, sub_f, "#94a3b8")
    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "building-top-view.png", quality=95)
    print("wrote building-top-view.png")


def compose_cube_side() -> None:
    src = BASE / "cube-side-base.png"
    if not src.exists():
        return
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_f, sub_f = font(38, bold=True), font(20)
    draw.rectangle([0, 0, w, 88], fill=(15, 23, 42, 190))
    center_text(draw, 12, "Куб — вид сбоку", w, title_f, "#f8fafc")
    center_text(draw, 50, "Sky tilt 25° · PTZ home зенит", w, sub_f, "#94a3b8")
    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(IMG / "cube-side-view.png", quality=95)
    print("wrote cube-side-view.png")


if __name__ == "__main__":
    compose_system_overview()
    compose_detection_flow()
    compose_network_topology()
    compose_cube_top()
    compose_building_top()
    compose_cube_side()
