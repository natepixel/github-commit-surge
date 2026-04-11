import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

const COHORTS = ["dormant_reactivated", "consistently_active", "new_surger", "always_sparse"];
const COLORS = {
  dormant_reactivated: "#e05c2a",
  consistently_active: "#3a86ff",
  new_surger:          "#8ac926",
  always_sparse:       "#aaa",
};

/**
 * Stacked area chart showing total commits per cohort per year.
 *
 * @param {string} containerId
 * @param {Array}  data         — timeline.json
 * @param {"absolute"|"percent"} mode
 */
export function renderTimeline(containerId, data, mode = "absolute") {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  // Normalize to percentage if requested
  const rows = [];
  for (const record of data) {
    const total = record.total || 1;
    for (const cohort of COHORTS) {
      const raw = record[cohort] ?? 0;
      rows.push({
        year: record.year,
        cohort,
        value: mode === "percent" ? (raw / total) * 100 : raw,
      });
    }
  }

  const plot = Plot.plot({
    width: container.clientWidth || 900,
    height: 340,
    marginLeft: 60,
    marginRight: 20,
    style: { background: "transparent", color: "#e6edf3", fontSize: "12px" },
    x: {
      label: "Year",
      tickFormat: d => String(d),
      grid: true,
    },
    y: {
      label: mode === "percent" ? "Share of total commits (%)" : "Total commits",
      grid: true,
      tickFormat: mode === "percent"
        ? d => `${d.toFixed(0)}%`
        : d => d >= 1e6 ? `${(d/1e6).toFixed(1)}M` : d >= 1000 ? `${(d/1000).toFixed(0)}k` : d,
    },
    color: {
      domain: COHORTS,
      range: COHORTS.map(c => COLORS[c]),
    },
    marks: [
      Plot.areaY(rows, Plot.stackY({
        x: "year",
        y: "value",
        fill: "cohort",
        fillOpacity: 0.85,
        order: COHORTS,
        curve: "monotone-x",
      })),
      Plot.lineY(rows, Plot.stackY({
        x: "year",
        y: "value",
        stroke: "cohort",
        strokeWidth: 1,
        order: COHORTS,
        curve: "monotone-x",
      })),
      // Copilot GA reference line
      Plot.ruleX([2022], { stroke: "#fff", strokeDasharray: "4,3", strokeWidth: 1 }),
      Plot.text([{ year: 2022, label: "Copilot GA" }], {
        x: "year",
        y: mode === "percent" ? 95 : null,
        text: "label",
        fill: "#8b949e",
        fontSize: 10,
        dx: 4,
        frameAnchor: mode === "percent" ? "top-left" : "top-right",
      }),
    ],
  });

  container.appendChild(plot);
}
