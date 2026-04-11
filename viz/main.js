import { renderCohortCurves, buildLegend } from "./charts/cohort_curves.js";
import { renderTimeline }                  from "./charts/timeline.js";
import { renderScatter }                   from "./charts/scatter.js";
import { renderInflection }                from "./charts/inflection.js";

// ── Data paths ───────────────────────────────────────────────────────────────
// When running locally without a server, you can serve data/ via:
//   python3 -m http.server 8000
// Or symlink viz/data → data/viz after running pipeline step 05.

const DATA_BASE = "./data";

function fetchJSON(path) {
  return fetch(path).then(r => {
    if (!r.ok) throw new Error(`Failed to load ${path}: ${r.status}`);
    return r.json();
  });
}

function showError(containerId, message) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="error">${message}</div>`;
}

function showLoading(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="loading">Loading data…</div>`;
}

// ── Summary stats ────────────────────────────────────────────────────────────
function populateSummary(summary) {
  const fmt = n => n?.toLocaleString() ?? "—";
  document.getElementById("stat-total").textContent        = fmt(summary.total_users_analyzed);
  document.getElementById("stat-dormant-pct").textContent  = `${summary.dormant_reactivated_pct}%`;
  document.getElementById("stat-surge-ratio").textContent  = `${summary.median_surge_ratio_dormant}×`;
  document.getElementById("stat-peak-year").textContent    = summary.peak_inflection_year ?? "—";
}

// ── Demo / placeholder data ──────────────────────────────────────────────────
// Used when real data files don't exist yet (i.e., before the pipeline runs).
// This lets you see the charts immediately after cloning.

function makeDemoData() {
  const years = Array.from({ length: 15 }, (_, i) => 2011 + i);
  const cohorts = {
    dormant_reactivated: years.map(y => ({
      year: y,
      p25: y < 2019 ? 0 : y < 2022 ? 5 : (y - 2021) * 40,
      p50: y < 2019 ? 2 : y < 2022 ? 8 : (y - 2021) * 80,
      p75: y < 2019 ? 8 : y < 2022 ? 20 : (y - 2021) * 140,
      mean: y < 2019 ? 3 : y < 2022 ? 10 : (y - 2021) * 90,
      n: 800,
    })),
    consistently_active: years.map(y => ({
      year: y,
      p25: 80 + y * 2,
      p50: 180 + y * 5,
      p75: 400 + y * 10,
      mean: 200 + y * 6,
      n: 1200,
    })),
    new_surger: years.map(y => ({
      year: y,
      p25: y < 2020 ? 0 : (y - 2019) * 15,
      p50: y < 2020 ? 0 : (y - 2019) * 35,
      p75: y < 2020 ? 2 : (y - 2019) * 70,
      mean: y < 2020 ? 0 : (y - 2019) * 40,
      n: 600,
    })),
    always_sparse: years.map(y => ({
      year: y,
      p25: 0, p50: 1, p75: 4, mean: 2, n: 3000,
    })),
  };

  const meta = {
    labels: {
      dormant_reactivated: "Dormant → Reactivated",
      consistently_active: "Consistently Active",
      new_surger:          "New Surger",
      always_sparse:       "Always Sparse",
    },
    colors: {
      dormant_reactivated: "#e05c2a",
      consistently_active: "#3a86ff",
      new_surger:          "#8ac926",
      always_sparse:       "#888",
    },
    ai_milestones: [
      { year: 2021, label: "Copilot Preview" },
      { year: 2022, label: "Copilot GA" },
      { year: 2023, label: "ChatGPT / Claude" },
      { year: 2024, label: "AI agent surge" },
    ],
  };

  const scatter = Array.from({ length: 600 }, (_, i) => {
    const cohorts = ["dormant_reactivated", "consistently_active", "new_surger"];
    const cohort = cohorts[i % 3];
    const account_age = Math.floor(Math.random() * 18) + 2;
    return {
      login: `user_${i}`,
      account_age,
      account_year: 2022 - account_age,
      surge_magnitude: cohort === "dormant_reactivated"
        ? Math.floor(Math.random() * 800 + 50)
        : cohort === "consistently_active"
        ? Math.floor(Math.random() * 400 + 20)
        : Math.floor(Math.random() * 300 + 10),
      surge_ratio: Math.round(Math.random() * 20 + 1),
      inflection_year: 2021 + Math.floor(Math.random() * 4),
      lifetime_commits: Math.floor(Math.random() * 5000 + 100),
      cohort,
    };
  });

  const timeline = years.map(y => ({
    year: y,
    dormant_reactivated: y < 2019 ? 200 : y < 2022 ? 600 : (y - 2020) * 8000,
    consistently_active: 40000 + y * 500,
    new_surger: y < 2020 ? 0 : (y - 2019) * 3000,
    always_sparse: 5000,
    total: 0,
  })).map(r => ({ ...r, total: r.dormant_reactivated + r.consistently_active + r.new_surger + r.always_sparse }));

  const inflection = [
    { year: 2019, count: 45 },
    { year: 2020, count: 78 },
    { year: 2021, count: 130 },
    { year: 2022, count: 290 },
    { year: 2023, count: 520 },
    { year: 2024, count: 410 },
    { year: 2025, count: 180 },
  ];

  const summary = {
    total_users_analyzed: 8420,
    dormant_reactivated_pct: 12.4,
    median_surge_ratio_dormant: 18.3,
    peak_inflection_year: 2023,
  };

  return { curves: { cohorts, meta }, scatter, timeline, inflection, summary };
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  // Show loading spinners
  ["chart-curves", "chart-timeline", "chart-scatter", "chart-inflection"]
    .forEach(showLoading);

  let curves, scatter, timeline, inflection, summary;

  try {
    [curves, scatter, timeline, inflection, summary] = await Promise.all([
      fetchJSON(`${DATA_BASE}/cohort_curves.json`),
      fetchJSON(`${DATA_BASE}/scatter_data.json`),
      fetchJSON(`${DATA_BASE}/timeline.json`),
      fetchJSON(`${DATA_BASE}/inflection_histogram.json`),
      fetchJSON(`${DATA_BASE}/summary.json`),
    ]);
    console.log("Loaded real data.");
  } catch (err) {
    console.warn("Real data not found, using demo data:", err.message);
    const demo = makeDemoData();
    curves    = demo.curves;
    scatter   = demo.scatter;
    timeline  = demo.timeline;
    inflection = demo.inflection;
    summary   = demo.summary;

    // Show a subtle banner
    document.querySelector(".subtitle").textContent +=
      " · (demo data — run pipeline to load real results)";
  }

  // Render all charts
  populateSummary(summary);
  buildLegend("legend-curves", "chart-curves", curves);
  renderCohortCurves("chart-curves", curves);
  renderTimeline("chart-timeline", timeline);
  renderScatter("chart-scatter", scatter);
  renderInflection("chart-inflection", inflection);

  // Timeline mode toggle
  document.querySelectorAll("input[name='timeline-mode']").forEach(radio => {
    radio.addEventListener("change", () => {
      renderTimeline("chart-timeline", timeline, radio.value);
    });
  });

  // Re-render on resize (debounced)
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      renderCohortCurves("chart-curves", curves);
      renderTimeline("chart-timeline", timeline,
        document.querySelector("input[name='timeline-mode']:checked").value);
      renderScatter("chart-scatter", scatter);
      renderInflection("chart-inflection", inflection);
    }, 200);
  });
}

main().catch(err => {
  console.error(err);
  ["chart-curves", "chart-timeline", "chart-scatter", "chart-inflection"]
    .forEach(id => showError(id, `Render error: ${err.message}`));
});
