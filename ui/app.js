(function () {
  const API = "/api";
  const SIM = "/sim";

  const els = {
    modeBadge: document.getElementById("modeBadge"),
    statusPill: document.getElementById("statusPill"),
    statTracks: document.getElementById("statTracks"),
    statTargets: document.getElementById("statTargets"),
    statSky: document.getElementById("statSky"),
    statPtz: document.getElementById("statPtz"),
    statTurrets: document.getElementById("statTurrets"),
    tracksTable: document.querySelector("#tracksTable tbody"),
    targetsTable: document.querySelector("#targetsTable tbody"),
    mapCanvas: document.getElementById("mapCanvas"),
    siteLayout: document.getElementById("siteLayout"),
    turretList: document.getElementById("turretList"),
    calibJob: document.getElementById("calibJob"),
    calibTitle: document.getElementById("calibTitle"),
    calibSteps: document.getElementById("calibSteps"),
    calibReco: document.getElementById("calibReco"),
    simState: document.getElementById("simState"),
  };

  const map = window.createMapRenderer(els.mapCanvas);
  let calibPollTimer = null;

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("panel-" + btn.dataset.tab).classList.add("active");
    });
  });

  document.getElementById("showTrails").addEventListener("change", (e) => {
    map.setOptions({ trails: e.target.checked });
  });
  document.getElementById("showLabels").addEventListener("change", (e) => {
    map.setOptions({ labels: e.target.checked });
  });

  async function api(path, opts) {
    const r = await fetch(API + path, opts);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function simApi(path, opts) {
    const r = await fetch(SIM + path, opts);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  function onFrame(frame) {
    const st = frame.status || {};
    els.modeBadge.textContent = frame.mode || "live";
    els.modeBadge.classList.toggle("simulation", frame.mode === "simulation");
    els.statusPill.textContent = st.pipeline_running ? "pipeline OK" : "stopped";
    els.statTracks.textContent = (frame.tracks || []).length;
    els.statTargets.textContent = (frame.targets || []).length;
    els.statSky.textContent = st.sky_cameras_online ?? "—";
    els.statPtz.textContent = st.ptz_cameras_online ?? "—";
    els.statTurrets.textContent = st.turret_count ?? "—";

    els.tracksTable.innerHTML = (frame.tracks || [])
      .map(
        (t) =>
          `<tr><td>${t.id}</td><td>${t.class_name}</td><td>${(t.confidence * 100).toFixed(0)}%</td><td>${t.az_deg.toFixed(1)}°</td><td>${t.el_deg.toFixed(1)}°</td></tr>`
      )
      .join("");

    els.targetsTable.innerHTML = (frame.targets || [])
      .map((t) => {
        const enu = t.position_enu_m.map((v) => v.toFixed(1)).join(", ");
        return `<tr><td>${t.target_id}</td><td>${t.class_name}</td><td>${enu}</td><td>${(t.confidence * 100).toFixed(0)}%</td></tr>`;
      })
      .join("");

    map.render(frame);
  }

  function connectWs() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(proto + "//" + location.host + "/ws/core");
    ws.onmessage = (ev) => {
      try {
        onFrame(JSON.parse(ev.data));
      } catch (e) {
        console.warn(e);
      }
    };
    ws.onclose = () => setTimeout(connectWs, 2000);
  }

  async function loadSettings() {
    try {
      const layout = await api("/v1/site/layout");
      map.setLayout(layout);
      els.siteLayout.textContent = JSON.stringify(layout, null, 2);
      const turrets = await api("/v1/turrets");
      els.turretList.textContent = JSON.stringify(turrets, null, 2);
    } catch (e) {
      els.siteLayout.textContent = "Ошибка: " + e.message;
    }
  }

  document.querySelectorAll("[data-scope]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const scope = btn.dataset.scope;
      try {
        const job = await api("/v1/calibration/auto/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scope }),
        });
        showCalibJob(job);
        pollCalib(job.job_id);
      } catch (e) {
        alert(e.message);
      }
    });
  });

  function showCalibJob(job) {
    els.calibJob.classList.remove("hidden");
    els.calibTitle.textContent = `Калибровка: ${job.scope} (${job.id || job.job_id})`;
    renderCalibSteps(job.steps || []);
    els.calibReco.textContent = JSON.stringify(job.recommendations || {}, null, 2);
  }

  function renderCalibSteps(steps) {
    els.calibSteps.innerHTML = steps
      .map((s) => `<li class="${s.status}">${s.title} — ${s.status}</li>`)
      .join("");
  }

  function pollCalib(jobId) {
    if (calibPollTimer) clearInterval(calibPollTimer);
    calibPollTimer = setInterval(async () => {
      try {
        const job = await api("/v1/calibration/jobs/" + jobId);
        showCalibJob(job);
        if (job.status === "done") clearInterval(calibPollTimer);
      } catch (_) {}
    }, 800);
  }

  document.getElementById("btnSimStart").addEventListener("click", async () => {
    const scenario = document.getElementById("scenarioSelect").value;
    try {
      const st = await simApi("/scenario/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
      els.simState.textContent = JSON.stringify(st, null, 2);
    } catch (e) {
      els.simState.textContent = "Ошибка: " + e.message;
    }
  });

  document.getElementById("btnSimStop").addEventListener("click", async () => {
    try {
      await simApi("/scenario/stop", { method: "POST" });
      els.simState.textContent = "Сценарий остановлен";
    } catch (e) {
      els.simState.textContent = "Ошибка: " + e.message;
    }
  });

  document.getElementById("btnModeSim").addEventListener("click", async () => {
    await api("/v1/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "simulation" }),
    });
  });

  document.getElementById("btnModeLive").addEventListener("click", async () => {
    await api("/v1/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "live" }),
    });
  });

  connectWs();
  loadSettings();
})();
