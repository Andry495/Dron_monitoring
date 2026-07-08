import { Resvg } from '@resvg/resvg-js';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, extname } from 'path';

const dir = join('docs', 'images');
const widths = {
  'system-overview.svg': 1440,
  'cube-top-view.svg': 1440,
  'cube-side-view.svg': 1520,
  'detection-flow.svg': 1920,
  'network-topology.svg': 1800,
  'turret-overview.svg': 1440,
  'turret-engagement.svg': 1440,
  'dead-zones-top.svg': 1440,
  'dead-zones-elevation.svg': 1600,
  'dead-zones-layers.svg': 1800,
};

for (const file of readdirSync(dir)) {
  if (extname(file) !== '.svg') continue;
  const svg = readFileSync(join(dir, file), 'utf8');
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: widths[file] ?? 1440 },
    font: { loadSystemFonts: true },
  });
  const png = resvg.render().asPng();
  const out = join(dir, file.replace('.svg', '.png'));
  writeFileSync(out, png);
  console.log('wrote', out);
}
