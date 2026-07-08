import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dir, '..', 'docs', 'images');
const fontDir = join(__dir, 'fonts');
mkdirSync(outDir, { recursive: true });

if (!existsSync(join(fontDir, 'Arial.ttf'))) {
  console.warn('⚠ scripts/fonts/Arial.ttf не найден — PNG могут без кириллицы. Скопируйте из %WINDIR%\\Fonts\\');
}

const F = 'Arial';

const defsCommon = `
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="45%" stop-color="#1e1b4b"/>
      <stop offset="100%" stop-color="#082f49"/>
    </linearGradient>
    <linearGradient id="cardTeal" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#14b8a6"/><stop offset="100%" stop-color="#0f766e"/></linearGradient>
    <linearGradient id="cardPurple" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#a78bfa"/><stop offset="100%" stop-color="#6d28d9"/></linearGradient>
    <linearGradient id="cardBlue" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0369a1"/></linearGradient>
    <linearGradient id="cardOrange" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fb923c"/><stop offset="100%" stop-color="#c2410c"/></linearGradient>
    <linearGradient id="cardGray" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#64748b"/><stop offset="100%" stop-color="#334155"/></linearGradient>
    <linearGradient id="cardHub" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fcd34d"/><stop offset="100%" stop-color="#b45309"/></linearGradient>
    <linearGradient id="skyG" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#4ade80"/><stop offset="100%" stop-color="#15803d"/></linearGradient>
    <linearGradient id="ptzG" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#1d4ed8"/></linearGradient>
    <radialGradient id="skyZone" cx="50%" cy="40%" r="55%"><stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/><stop offset="100%" stop-color="#0ea5e9" stop-opacity="0"/></radialGradient>
    <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.45"/></filter>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <marker id="arr" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#94a3b8"/></marker>
  </defs>`;

function open(w, h) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" font-family="${F}, sans-serif">
${defsCommon}
  <rect width="${w}" height="${h}" fill="url(#bg)"/>`;
}
function close() { return '\n</svg>'; }

function t(x, y, text, o = {}) {
  const { size = 12, fill = '#e2e8f0', anchor = 'start', weight = 400 } = o;
  return `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" text-anchor="${anchor}" font-weight="${weight}">${text}</text>`;
}

function card(x, y, w, h, title, lines, grad, stroke, titleFill = '#fff') {
  const lh = 15;
  const startY = y + (h - lines.length * lh) / 2 + 8;
  return `
  <rect x="${x + 5}" y="${y + 6}" width="${w}" height="${h}" rx="14" fill="#000" opacity="0.3"/>
  <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" fill="url(#${grad})" stroke="${stroke}" stroke-width="2.5" filter="url(#shadow)"/>
  ${t(x + w / 2, startY - 6, title, { size: 15, anchor: 'middle', weight: 700, fill: titleFill })}
  ${lines.map((l, i) => t(x + w / 2, startY + i * lh + 10, l, { size: 11, anchor: 'middle', fill: '#f1f5f9' })).join('')}`;
}

function skyIcon(x, y, label) {
  return `<g transform="translate(${x},${y})" filter="url(#shadow)">
    <circle r="18" fill="url(#skyG)" stroke="#86efac" stroke-width="2"/>
    <polygon points="0,-12 8,7 -8,7" fill="#dcfce7"/>
    <circle r="4" cy="2" fill="#14532d" opacity="0.4"/>
    ${t(0, 34, label, { size: 10, anchor: 'middle', weight: 700, fill: '#86efac' })}
  </g>`;
}

function ptzIcon(x, y, label = 'PTZ') {
  return `<g transform="translate(${x},${y})" filter="url(#shadow)">
    <circle r="20" fill="url(#ptzG)" stroke="#93c5fd" stroke-width="2"/>
    <polygon points="0,-14 10,9 -10,9" fill="#dbeafe"/>
    <rect x="-7" y="9" width="14" height="7" rx="2" fill="#1e3a8a"/>
    ${label ? t(0, 38, label, { size: 10, anchor: 'middle', weight: 700, fill: '#93c5fd' }) : ''}
  </g>`;
}

function hubIcon(x, y, lines) {
  return `<g transform="translate(${x},${y})" filter="url(#glow)">
    <ellipse rx="54" ry="30" fill="#1e293b" stroke="url(#cardHub)" stroke-width="3"/>
    <ellipse rx="40" ry="18" cy="-6" fill="#334155" stroke="#fbbf24" stroke-width="1.5"/>
    ${lines.map((l, i) => t(0, -2 + i * 14, l, { size: i === 0 ? 12 : 9, anchor: 'middle', weight: i === 0 ? 700 : 400, fill: i === 0 ? '#fbbf24' : '#94a3b8' })).join('')}
  </g>`;
}

function arrow(x1, y1, x2, y2, c = '#64748b', dash = '') {
  const d = dash ? ` stroke-dasharray="${dash}"` : '';
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="2.5" marker-end="url(#arr)"${d}/>`;
}

function wedge(cx, cy, r, a0, a1, fill, op = 0.4) {
  const rad = (a) => ((a - 90) * Math.PI) / 180;
  const x1 = cx + r * Math.cos(rad(a0)), y1 = cy + r * Math.sin(rad(a0));
  const x2 = cx + r * Math.cos(rad(a1)), y2 = cy + r * Math.sin(rad(a1));
  const lg = a1 - a0 > 180 ? 1 : 0;
  return `<path d="M${cx} ${cy}L${x1} ${y1}A${r} ${r} 0 ${lg} 1 ${x2} ${y2}Z" fill="${fill}" opacity="${op}"/>`;
}

const files = {};

// ═══ system-overview — презентационный слайд ═══
files['system-overview.svg'] = open(960, 580) + `
  ${t(480, 40, 'Dron Monitoring — комплект v1', { size: 26, anchor: 'middle', weight: 700, fill: '#f8fafc' })}
  ${t(480, 66, '4× Sky fixed + 4× PTZ 25× · mini-PC · ai-engine · operator-ui · симулятор', { size: 13, anchor: 'middle', fill: '#94a3b8' })}

  <ellipse cx="480" cy="118" rx="320" ry="50" fill="url(#skyZone)"/>
  ${t(480, 116, 'зона обзора / видимости', { size: 14, anchor: 'middle', weight: 700, fill: '#7dd3fc' })}

  <rect x="250" y="145" width="460" height="230" rx="16" fill="#111827" stroke="#475569" stroke-width="3" filter="url(#shadow)"/>
  ${t(480, 172, 'периметр поста (cube_compact / building_corners)', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${ptzIcon(290, 195)}
  ${ptzIcon(670, 195)}
  ${ptzIcon(290, 325)}
  ${ptzIcon(670, 325)}

  ${skyIcon(400, 230, 'Sky-N')}
  ${skyIcon(560, 230, 'Sky-E')}
  ${skyIcon(400, 300, 'Sky-W')}
  ${skyIcon(560, 300, 'Sky-S')}

  ${hubIcon(480, 268, ['купол-hub', 'ПК + switch'])}

  ${card(50, 420, 155, 88, 'mini-PC', ['monitor-core', 'recorder · API'], 'cardTeal', '#5eead4')}
  ${card(225, 420, 155, 88, 'ai-engine', ['детект · класс', 'ONNX CPU'], 'cardPurple', '#c4b5fd')}
  ${card(400, 420, 155, 88, 'operator-ui', ['карта · калибр.', ':3000'], 'cardBlue', '#7dd3fc')}
  ${card(575, 420, 155, 88, 'simulator', ['сценарии', ':8070'], 'cardOrange', '#fdba74')}
  ${card(750, 420, 160, 88, 'Switch 12p', ['8 камер + ПК', 'без PoE'], 'cardGray', '#94a3b8')}

  ${arrow(205, 464, 225, 464)}
  ${arrow(380, 464, 400, 464)}
  ${arrow(555, 464, 575, 464)}
  ${arrow(730, 464, 750, 464)}
  ${arrow(830, 420, 480, 375, '#64748b', '6 4')}

  <rect x="620" y="155" width="200" height="72" rx="12" fill="#1e293b" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(720, 180, 'без ESP32 · без MQTT', { size: 12, anchor: 'middle', weight: 700, fill: '#e2e8f0' })}
  ${t(720, 200, 'PTZ: ONVIF pan/tilt/zoom', { size: 10, anchor: 'middle', fill: '#94a3b8' })}
  ${t(720, 216, 'турель 0..N · fleet', { size: 10, anchor: 'middle', fill: '#fca5a5' })}
  ${t(720, 232, '~252 000 ₽ камеры', { size: 10, anchor: 'middle', fill: '#64748b' })}
` + close();

// ═══ detection-flow ═══
files['detection-flow.svg'] = open(1000, 400) + `
  ${t(500, 36, 'Поток обработки v1', { size: 24, anchor: 'middle', weight: 700, fill: '#f8fafc' })}
  ${t(500, 60, 'live: RTSP · simulation: scenario-simulator', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${[
    [30, '4× Sky', 'RTSP', 'cardTeal', '#5eead4'],
    [150, 'ai-engine', '/detect', 'cardPurple', '#c4b5fd'],
    [270, 'tracker', 'az/el', 'cardBlue', '#7dd3fc'],
    [390, 'PTZ', 'ONVIF', 'cardGray', '#94a3b8'],
    [510, 'zoom', 'main', 'cardBlue', '#60a5fa'],
    [630, 'ai-engine', '/classify', 'cardPurple', '#c4b5fd'],
    [750, 'geolocate', '2× PTZ', 'cardTeal', '#5eead4'],
    [870, 'UI / WS', 'оператор', 'cardOrange', '#fdba74'],
  ].map(([x, a, b, g, s]) => card(x, 110, 105, 72, a, [b], g, s)).join('')}

  ${[135, 255, 375, 495, 615, 735, 855].map((x, i, a) => i < a.length ? arrow(x, 146, a[i], 146) : '').join('')}

  ${card(30, 220, 200, 60, 'simulator', ['feed детекций'], 'cardOrange', '#fdba74')}
  ${arrow(130, 220, 175, 182, '#f59e0b', '5 4')}

  <rect x="260" y="310" width="480" height="65" rx="14" fill="#111827" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(500, 338, 'monitor-core — цикл 10 Hz · турель fleet · автокалибровка', { size: 13, anchor: 'middle', weight: 700, fill: '#e2e8f0' })}
  ${t(500, 358, 'запись · каталог — roadmap', { size: 10, anchor: 'middle', fill: '#64748b' })}
` + close();

// ═══ cube-top-view ═══
files['cube-top-view.svg'] = open(760, 560) + `
  ${t(380, 38, 'Вид сверху — cube_compact', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(380, 62, 'Sky: середины сторон · PTZ: углы · overlap 15–25%', { size: 12, anchor: 'middle', fill: '#94a3b8' })}
  <line x1="380" y1="80" x2="380" y2="115" stroke="#38bdf8" stroke-width="3"/>
  ${t(380, 76, 'N', { size: 16, anchor: 'middle', weight: 700, fill: '#38bdf8' })}

  <rect x="160" y="140" width="440" height="360" rx="14" fill="#111827" stroke="#64748b" stroke-width="3" filter="url(#shadow)"/>
  ${t(380, 168, 'верхняя грань куба ~1×1 m', { size: 12, anchor: 'middle', fill: '#64748b' })}

  ${ptzIcon(200, 180, 'NW')}
  ${ptzIcon(560, 180, 'NE')}
  ${ptzIcon(200, 460, 'SW')}
  ${ptzIcon(560, 460, 'SE')}

  ${skyIcon(380, 175, 'Sky-N')}
  ${skyIcon(555, 320, 'Sky-E')}
  ${skyIcon(380, 465, 'Sky-S')}
  ${skyIcon(205, 320, 'Sky-W')}

  ${[[380, 320, 0], [555, 320, 90], [380, 465, 180], [205, 320, 270]].map(([x, y, az]) =>
    wedge(x, y, 70, az - 52, az + 52, '#22c55e', 0.25)).join('')}

  ${t(380, 530, 'зелёный = Sky · синий = PTZ', { size: 11, anchor: 'middle', fill: '#64748b' })}
` + close();

// ═══ cube-side-view ═══
files['cube-side-view.svg'] = open(800, 520) + `
  ${t(400, 36, 'Куб — вид сбоку', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(400, 60, 'Sky tilt 25° · PTZ home зенит', { size: 12, anchor: 'middle', fill: '#94a3b8' })}
  <rect x="0" y="80" width="800" height="120" fill="url(#skyZone)"/>
  ${t(400, 130, 'небо', { size: 18, anchor: 'middle', weight: 700, fill: '#7dd3fc' })}

  <g transform="translate(120,210)">${skyIcon(0, 0, 'Sky')}</g>
  <g transform="translate(400,200)">${ptzIcon(0, 0, 'PTZ')}</g>

  <rect x="70" y="260" width="660" height="160" rx="14" fill="#1f2937" stroke="#64748b" stroke-width="3" filter="url(#shadow)"/>
  ${t(400, 345, 'куб / рама V-slot ~1 m', { size: 15, anchor: 'middle', weight: 700, fill: '#cbd5e1' })}

  <line x1="120" y1="210" x2="300" y2="130" stroke="#4ade80" stroke-width="3" stroke-dasharray="8 5"/>
  ${t(310, 125, 'tilt 25°', { size: 12, fill: '#86efac', weight: 700 })}
  <line x1="400" y1="200" x2="580" y2="115" stroke="#fbbf24" stroke-width="3" stroke-dasharray="8 5"/>
  ${t(590, 110, 'pan/tilt', { size: 12, fill: '#fbbf24', weight: 700 })}

  <line x1="0" y1="440" x2="800" y2="440" stroke="#4ade80" stroke-width="3"/>
  ${t(400, 468, 'земля / крыша', { size: 14, anchor: 'middle', weight: 700, fill: '#86efac' })}
` + close();

// ═══ building-top-view ═══
files['building-top-view.svg'] = open(760, 580) + `
  ${t(380, 38, 'Вид сверху — building_corners', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(380, 62, '4 угла: Sky+PTZ · центр: купол-hub', { size: 12, anchor: 'middle', fill: '#94a3b8' })}
  <line x1="380" y1="82" x2="380" y2="112" stroke="#38bdf8" stroke-width="3"/>
  ${t(380, 78, 'N', { size: 16, anchor: 'middle', weight: 700, fill: '#38bdf8' })}

  <rect x="100" y="130" width="560" height="380" rx="16" fill="none" stroke="#64748b" stroke-width="3" filter="url(#shadow)"/>
  ${t(380, 158, 'контур кровли здания', { size: 12, anchor: 'middle', fill: '#64748b' })}

  ${[[150, 170, 'NE'], [610, 170, 'SE'], [150, 470, 'SW'], [610, 470, 'NW']].map(([x, y, c]) =>
    `<g transform="translate(${x},${y})"><circle r="24" fill="url(#ptzG)" stroke="#93c5fd" stroke-width="2"/><circle r="14" fill="url(#skyG)"/>${t(0, 40, c, { size: 10, anchor: 'middle', weight: 700 })}</g>`).join('')}

  ${hubIcon(380, 320, ['купол-hub', 'ENU · mini-PC'])}

  <g transform="translate(300,520)"><circle r="14" fill="#dc2626" opacity="0.7"/>${t(0, 4, 'T1', { size: 9, anchor: 'middle', fill: '#fff', weight: 700 })}</g>
  <g transform="translate(460,520)"><circle r="14" fill="#dc2626" opacity="0.7"/>${t(0, 4, 'T2', { size: 9, anchor: 'middle', fill: '#fff', weight: 700 })}</g>
  ${t(380, 560, 'турели 0..N · site.building.example.yaml', { size: 11, anchor: 'middle', fill: '#64748b' })}
` + close();

// ═══ network-topology ═══
files['network-topology.svg'] = open(940, 540) + `
  ${t(470, 36, 'Сеть v1 — 192.168.10.0/24', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(470, 60, 'Switch 12p · 9 портов · питание 12 V отдельно', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${card(370, 250, 200, 85, 'Switch 12p', ['без PoE'], 'cardGray', '#94a3b8')}
  ${card(80, 255, 160, 75, 'mini-PC .10', ['core·ai·ui'], 'cardTeal', '#5eead4')}
  ${card(620, 80, 140, 55, 'Sky .11–.14', [], 'cardTeal', '#4ade80', '#ecfdf5')}
  ${card(620, 155, 140, 55, 'PTZ .21–.24', [], 'cardBlue', '#60a5fa', '#eff6ff')}
  ${card(620, 230, 140, 55, 'turret .30+', [], 'cardOrange', '#f87171', '#fff1f2')}

  ${arrow(240, 292, 370, 292)}
  ${arrow(570, 292, 620, 107)}
  ${arrow(570, 292, 620, 182)}
  ${arrow(570, 292, 620, 257)}

  <rect x="60" y="370" width="820" height="140" rx="14" fill="#111827" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(470, 400, 'Порты: 1→ПК · 2–5 Sky · 6–9 PTZ · 10–12 резерв/турели', { size: 13, anchor: 'middle', weight: 700, fill: '#e2e8f0' })}
  ${t(470, 428, 'Docker: :8080 core · :8090 ai · :3000 UI · :8070 sim', { size: 11, anchor: 'middle', fill: '#94a3b8' })}
` + close();

// ═══ dead-zones-top ═══
files['dead-zones-top.svg'] = open(760, 760) + `
  ${t(380, 38, 'Мёртвые зоны — азимут', { size: 22, anchor: 'middle', weight: 700 })}
  ${t(380, 62, 'cube_compact · HFOV 105° · overlap 20%', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  <circle cx="380" cy="400" r="300" fill="#0f172a" stroke="#334155" stroke-width="2"/>
  ${wedge(380, 400, 300, 327, 57, '#22c55e', 0.45)}
  ${wedge(380, 400, 300, 57, 147, '#16a34a', 0.4)}
  ${wedge(380, 400, 300, 147, 237, '#15803d', 0.35)}
  ${wedge(380, 400, 300, 237, 327, '#14532d', 0.3)}

  ${t(380, 108, 'N', { size: 18, anchor: 'middle', weight: 700, fill: '#38bdf8' })}
  ${t(660, 404, 'E', { size: 14, anchor: 'middle', fill: '#94a3b8' })}
  ${t(380, 700, 'S', { size: 14, anchor: 'middle', fill: '#94a3b8' })}
  ${t(100, 404, 'W', { size: 14, anchor: 'middle', fill: '#94a3b8' })}

  ${[45, 135, 225, 315].map((az) => {
    const rad = ((az - 90) * Math.PI) / 180;
    return `<line x1="380" y1="400" x2="${380 + 300 * Math.cos(rad)}" y2="${400 + 300 * Math.sin(rad)}" stroke="#f87171" stroke-width="2" stroke-dasharray="6 4"/>`;
  }).join('')}

  <rect x="350" y="370" width="60" height="60" rx="6" fill="#475569" stroke="#94a3b8" stroke-width="2" filter="url(#shadow)"/>
  ${t(380, 405, 'куб', { size: 11, anchor: 'middle', weight: 700, fill: '#f8fafc' })}

  ${t(90, 150, 'S1 швы', { size: 13, fill: '#fca5a5', weight: 700 })}
  ${t(90, 170, 'az 45° el 25–55°', { size: 10, fill: '#fecaca' })}
  ${t(90, 220, 'overlap ~21°', { size: 12, fill: '#86efac', weight: 700 })}
` + close();

// ═══ dead-zones-elevation ═══
files['dead-zones-elevation.svg'] = open(840, 520) + `
  ${t(420, 36, 'Мёртвые зоны — разрез по углу места', { size: 22, anchor: 'middle', weight: 700 })}
  ${t(420, 60, 'cube_compact · Sky tilt 25°', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  <line x1="80" y1="420" x2="780" y2="420" stroke="#4ade80" stroke-width="3"/>
  ${t(420, 448, 'горизонт el = 0°', { size: 14, anchor: 'middle', weight: 700, fill: '#86efac' })}

  <rect x="370" y="330" width="100" height="90" rx="8" fill="#475569" stroke="#94a3b8" stroke-width="2" filter="url(#shadow)"/>
  ${t(420, 382, 'куб', { size: 13, anchor: 'middle', weight: 700 })}

  <g transform="translate(420,310)">${skyIcon(0, 0, '')}</g>
  <line x1="420" y1="310" x2="560" y2="130" stroke="#4ade80" stroke-width="3" stroke-dasharray="8 5"/>
  <line x1="420" y1="310" x2="650" y2="220" stroke="#86efac" stroke-width="2" stroke-dasharray="5 4"/>
  ${t(570, 125, 'ось Sky 25°', { size: 12, fill: '#86efac', weight: 700 })}

  <rect x="560" y="130" width="190" height="55" rx="8" fill="#dc2626" opacity="0.25" stroke="#f87171"/>
  ${t(655, 162, 'A горизонт S3 · el 0–18°', { size: 11, anchor: 'middle', fill: '#fecaca' })}
  <rect x="560" y="205" width="190" height="65" rx="8" fill="#f59e0b" opacity="0.2" stroke="#fbbf24"/>
  ${t(655, 242, 'S1 шов · el 25–55°', { size: 11, anchor: 'middle', fill: '#fde047' })}
` + close();

// ═══ dead-zones-layers ═══
files['dead-zones-layers.svg'] = open(940, 460) + `
  ${t(470, 36, 'Слои покрытия', { size: 22, anchor: 'middle', weight: 700 })}
  ${t(470, 60, 'M motion · C класс · G гео · T турель', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${[[380, 150, '#22c55e', 'M+ Sky 88–92%'], [300, 120, '#eab308', 'M 75–85%'], [220, 95, '#2563eb', 'C PTZ 60–70%'], [150, 70, '#7c3aed', 'G geo 50–65%']].map(([rx, ry, c, lbl]) =>
    `<ellipse cx="470" cy="250" rx="${rx}" ry="${ry}" fill="none" stroke="${c}" stroke-width="3" opacity="0.6"/>${t(470 + rx + 15, 250 - ry + 20, lbl, { size: 10, fill: c, weight: 700 })}`).join('')}

  <ellipse cx="470" cy="250" rx="68" ry="40" fill="#dc2626" opacity="0.4" stroke="#fca5a5" stroke-width="2"/>
  ${t(470, 248, 'T турель', { size: 12, anchor: 'middle', weight: 700, fill: '#fff' })}
  ${t(470, 266, 'R 10–50 m', { size: 9, anchor: 'middle', fill: '#fecaca' })}

  <rect x="440" y="220" width="60" height="50" rx="6" fill="#475569" stroke="#94a3b8" filter="url(#shadow)"/>
  ${t(470, 252, 'куб', { size: 10, anchor: 'middle', weight: 700 })}
` + close();

// ═══ turret ═══
files['turret-overview.svg'] = open(960, 540) + `
  ${t(480, 36, 'Модуль турели — fleet', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(480, 60, 'опционально · R ≤ 50 m · site ENU', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${card(40, 110, 220, 110, 'monitor-core', ['turret/fleet.py', 'bind · track'], 'cardTeal', '#5eead4')}
  ${card(300, 95, 360, 140, 'turret-controller', ['bind · track · arm/safe', 'firmware'], 'cardOrange', '#fdba74')}
  ${card(700, 110, 220, 110, 'turret-sim', [':8030 dev'], 'cardGray', '#94a3b8')}

  ${arrow(260, 165, 300, 165)}
  ${arrow(660, 165, 700, 165)}

  <rect x="80" y="290" width="800" height="200" rx="16" fill="#111827" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(480, 322, 'Выбор модуля: ближайший в секторе · sticky target_id', { size: 14, anchor: 'middle', weight: 700, fill: '#fbbf24' })}
  ${card(140, 360, 170, 70, 'turret-01', ['.30'], 'cardOrange', '#f87171', '#fff')}
  ${card(340, 360, 170, 70, 'turret-02', ['.32'], 'cardOrange', '#f87171', '#fff')}
` + close();

files['turret-engagement.svg'] = open(960, 420) + `
  ${t(480, 36, 'Фазы поражения', { size: 24, anchor: 'middle', weight: 700 })}
  ${t(480, 60, 'cue → coarse → acquire → track → fire', { size: 12, anchor: 'middle', fill: '#94a3b8' })}

  ${[['CUE', 'cardGray', 70], ['COARSE', 'cardBlue', 230], ['ACQUIRE', 'cardPurple', 390], ['TRACK', 'cardTeal', 550], ['FIRE', 'cardOrange', 710]].map(([lbl, g, x]) =>
    card(x, 110, 130, 80, lbl, [], g, '#94a3b8', '#fff')).join('')}

  ${arrow(200, 150, 230, 150)}
  ${arrow(360, 150, 390, 150)}
  ${arrow(520, 150, 550, 150)}
  ${arrow(680, 150, 710, 150)}

  <rect x="120" y="230" width="720" height="140" rx="16" fill="#111827" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(480, 270, 't_go = t_полёта + t_раскрытия + t_задержки', { size: 15, anchor: 'middle', weight: 700, fill: '#e2e8f0' })}
  ${t(480, 300, 'SAFE по умолчанию · arm только оператором', { size: 12, anchor: 'middle', fill: '#fca5a5' })}
` + close();

files['software-stack.svg'] = open(960, 500) + `
  ${t(480, 36, 'Программный стек v1', { size: 24, anchor: 'middle', weight: 700 })}
  ${card(40, 90, 190, 90, 'operator-ui', [':3000'], 'cardBlue', '#7dd3fc')}
  ${card(250, 90, 190, 90, 'simulator', [':8070'], 'cardOrange', '#fdba74')}
  ${card(460, 90, 190, 90, 'monitor-core', [':8080'], 'cardTeal', '#5eead4')}
  ${card(670, 90, 190, 90, 'ai-engine', [':8090'], 'cardPurple', '#c4b5fd')}
  ${arrow(230, 135, 250, 135)}
  ${arrow(440, 135, 460, 135)}
  ${arrow(650, 135, 670, 135)}

  <rect x="60" y="220" width="840" height="240" rx="16" fill="#111827" stroke="#475569" stroke-width="2" filter="url(#shadow)"/>
  ${t(480, 252, 'monitor-core — модули', { size: 16, anchor: 'middle', weight: 700, fill: '#86efac' })}
  ${['sky_watch / sim_feed', 'tracker', 'ptz orchestrator', 'geolocate', 'turret fleet', 'calibration'].map((m, i) =>
    card(90 + (i % 3) * 280, 280 + Math.floor(i / 3) * 85, 250, 68, m, [], 'cardGray', '#64748b', '#f8fafc')).join('')}
` + close();

files['operator-console.svg'] = open(960, 400) + `
  ${t(480, 36, 'Консоль оператора', { size: 24, anchor: 'middle', weight: 700 })}
  ${['Обзор', 'Карта ENU', 'Калибровка', 'Симуляция', 'Настройки'].map((tab, i) =>
    card(40 + i * 180, 80, 155, 55, tab, [], 'cardGray', '#64748b', '#e2e8f0')).join('')}

  ${card(40, 180, 280, 100, 'operator-ui', ['прокси API'], 'cardBlue', '#7dd3fc')}
  ${card(360, 180, 280, 100, 'monitor-core', ['WS live'], 'cardTeal', '#5eead4')}
  ${card(680, 180, 240, 100, 'simulator', ['сценарии'], 'cardOrange', '#fdba74')}
  ${arrow(320, 230, 360, 230)}
  ${arrow(640, 230, 680, 230, '#f59e0b')}

  ${t(480, 340, 'симуляция: старт сценария → core/simulation → карта + треки', { size: 13, anchor: 'middle', fill: '#94a3b8' })}
` + close();

for (const [name, content] of Object.entries(files)) {
  writeFileSync(join(outDir, name), content, 'utf8');
  console.log('wrote', name);
}
