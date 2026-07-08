import { Resvg } from '@resvg/resvg-js';
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const dir = join(__dir, '..', 'docs', 'images');
const fontDir = join(__dir, 'fonts');

const arial = join(fontDir, 'Arial.ttf');
const arialBold = join(fontDir, 'Arial-Bold.ttf');

if (!existsSync(arial)) {
  console.error('Нужен scripts/fonts/Arial.ttf (copy из %WINDIR%\\Fonts\\)');
  process.exit(1);
}

const fontFiles = [arial];
if (existsSync(arialBold)) fontFiles.push(arialBold);

const widths = {
  'system-overview.svg': 1440,
  'software-stack.svg': 1440,
  'operator-console.svg': 1440,
  'cube-top-view.svg': 1440,
  'building-top-view.svg': 1440,
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
  if (!file.endsWith('.svg')) continue;
  const svg = readFileSync(join(dir, file), 'utf8');
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: widths[file] ?? 1440 },
    font: {
      fontFiles,
      loadSystemFonts: false,
      defaultFontFamily: 'Arial',
    },
  });
  const png = resvg.render().asPng();
  const out = join(dir, file.replace('.svg', '.png'));
  writeFileSync(out, png);
  console.log('wrote', out);
}
