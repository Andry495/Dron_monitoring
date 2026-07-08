/** Top-down ENU map renderer for operator console */

const CLASS_COLORS = {
  drone: "#3d9cf0",
  plane: "#a78bfa",
  unknown: "#8b9cb3",
};

function createMapRenderer(canvas) {
  const ctx = canvas.getContext("2d");
  let layout = null;
  let showTrails = true;
  let showLabels = true;
  const scale = 4; // px per meter

  function setLayout(siteLayout) {
    layout = siteLayout;
  }

  function setOptions({ trails, labels }) {
    if (trails !== undefined) showTrails = trails;
    if (labels !== undefined) showLabels = labels;
  }

  function enuToCanvas(e, n) {
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    return [cx + e * scale, cy - n * scale];
  }

  function drawGrid() {
    ctx.strokeStyle = "#1e2a3a";
    ctx.lineWidth = 1;
    const step = 20 * scale;
    for (let x = 0; x < canvas.width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  function drawSite() {
    if (!layout) return;
    const [hx, hy] = enuToCanvas(0, 0);
    ctx.fillStyle = "#2d3a4f";
    ctx.beginPath();
    ctx.arc(hx, hy, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#8b9cb3";
    ctx.font = "11px sans-serif";
    ctx.fillText("hub", hx + 10, hy + 4);

    for (const cam of layout.cameras || []) {
      const off = cam.offset_en_m || [0, 0];
      const [x, y] = enuToCanvas(off[0], off[1] || 0);
      ctx.fillStyle = cam.role === "sky" ? "#3dd68c" : "#f5a623";
      ctx.fillRect(x - 4, y - 4, 8, 8);
      if (showLabels) {
        ctx.fillStyle = "#6b7c93";
        ctx.font = "10px sans-serif";
        ctx.fillText(cam.id, x + 6, y - 6);
      }
    }

    for (const t of layout.turrets || []) {
      const off = t.offset_enu_m || [0, 0, 0];
      const [x, y] = enuToCanvas(off[0], off[1]);
      ctx.strokeStyle = t.enabled ? "#f05d5d" : "#555";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + 14, y);
      ctx.stroke();
      if (showLabels) {
        ctx.fillStyle = "#f05d5d";
        ctx.font = "10px sans-serif";
        ctx.fillText(t.id, x + 6, y + 12);
      }
    }
  }

  function drawObject(obj, isTrack) {
    const pos = obj.position_enu_m || obj.position_en_m;
    if (!pos) return;
    const [x, y] = enuToCanvas(pos[0], pos[1]);
    const cls = obj.class_name || obj.class || "unknown";
    const color = isTrack ? "#3dd68c" : CLASS_COLORS[cls] || CLASS_COLORS.unknown;

    if (showTrails && obj.trail && obj.trail.length > 1) {
      ctx.strokeStyle = color + "66";
      ctx.lineWidth = 2;
      ctx.beginPath();
      const [x0, y0] = enuToCanvas(obj.trail[0][0], obj.trail[0][1]);
      ctx.moveTo(x0, y0);
      for (let i = 1; i < obj.trail.length; i++) {
        const [xi, yi] = enuToCanvas(obj.trail[i][0], obj.trail[i][1]);
        ctx.lineTo(xi, yi);
      }
      ctx.stroke();
    }

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, isTrack ? 5 : 7, 0, Math.PI * 2);
    ctx.fill();

    if (showLabels) {
      const conf = obj.confidence != null ? ` ${(obj.confidence * 100).toFixed(0)}%` : "";
      ctx.fillStyle = "#e8eef7";
      ctx.font = "11px sans-serif";
      ctx.fillText(`${cls}${conf}`, x + 8, y - 8);
    }
  }

  function render(frame) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGrid();
    drawSite();

    for (const obj of frame.sim_objects || []) {
      drawObject(obj, false);
    }
    for (const t of frame.targets || []) {
      drawObject(
        {
          class_name: t.class_name,
          confidence: t.confidence,
          position_enu_m: t.position_enu_m,
        },
        false
      );
    }
    for (const t of frame.tracks || []) {
      if (t.position_enu_m) {
        drawObject(t, true);
      }
    }
  }

  return { setLayout, setOptions, render };
}

// Browser global for non-module script tag
if (typeof window !== "undefined") {
  window.createMapRenderer = createMapRenderer;
}
