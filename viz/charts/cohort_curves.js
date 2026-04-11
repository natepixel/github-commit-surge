import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

/**
 * Cohort velocity curves: median annual commits per user with IQR band.
 * One series per cohort. Vertical reference lines at AI milestones.
 *
 * @param {string} containerId
 * @param {object} data  — cohort_curves.json
 * @param {Set}    activeCohorts — set of cohort keys to render (for legend filtering)
 */
export function renderCohortCurves(containerId, data, activeCohorts = null) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  const { cohorts, meta } = data;
  const active = activeCohorts ?? new Set(Object.keys(cohorts));

  // Flatten to a single array for Plot
  const medianRows = [];
  const bandRows = [];

  for (const [key, records] of Object.entries(cohorts)) {
    if (!active.has(key)) continue;
    for (const r of records) {
      medianRows.push({ year: r.year, value: r.p50, cohort: key, n: r.n });
      bandRows.push({ year: r.year, lo: r.p25, hi: r.p75, cohort: key });
    }
  }

  const colorScale = Object.entries(meta.colors).map(([k, v]) => [k, v]).flat();

  const plot = Plot.plot({
    width: container.clientWidth || 900,
    height: 380,
    marginLeft: 60,
    marginRight: 20,
    style: { background: "transparent", color: "#e6edf3", fontSize: "12px" },
    x: {
      label: "Year",
      tickFormat: d => String(d),
      grid: true,
    },
    y: {
      label: "Median commits / year",
      grid: true,
      tickFormat: d => d >= 1000 ? `${(d/1000).toFixed(0)}k` : d,
    },
    color: {
      domain: Object.keys(meta.colors),
      range: Object.values(meta.colors),
    },
    marks: [
      // IQR bands
      Plot.areaY(bandRows, {
        x: "year",
        y1: "lo",
        y2: "hi",
        fill: "cohort",
        fillOpacity: 0.15,
        curve: "monotone-x",
      }),

      // Median lines
      Plot.lineY(medianRows, {
        x: "year",
        y: "value",
        stroke: "cohort",
        strokeWidth: 2.5,
        curve: "monotone-x",
      }),

      // Milestone reference lines
      ...meta.ai_milestones.map(m =>
        Plot.ruleX([m.year], {
          stroke: "#555",
          strokeDasharray: "4,3",
          strokeWidth: 1,
        })
      ),

      // Milestone labels (top of chart)
      Plot.text(meta.ai_milestones, {
        x: "year",
        y: 0,
        text: "label",
        fill: "#8b949e",
        fontSize: 10,
        rotate: -55,
        dy: -8,
        dx: 4,
        frameAnchor: "top-left",
      }),
    ],
  });

  container.appendChild(plot);
}


/** Build the legend DOM and wire up click-to-filter behavior. */
export function buildLegend(legendId, curveContainerId, data) {
  const legendEl = document.getElementById(legendId);
  const { meta } = data;
  const activeCohorts = new Set(Object.keys(meta.colors));

  for (const [key, label] of Object.entries(meta.labels)) {
    const item = document.createElement("div");
    item.className = "legend-item";
    item.dataset.cohort = key;

    const swatch = document.createElement("div");
    swatch.className = "legend-swatch";
    swatch.style.background = meta.colors[key];

    item.appendChild(swatch);
    item.appendChild(document.createTextNode(label));

    item.addEventListener("click", () => {
      if (activeCohorts.has(key)) {
        activeCohorts.delete(key);
        item.classList.add("dimmed");
      } else {
        activeCohorts.add(key);
        item.classList.remove("dimmed");
      }
      renderCohortCurves(curveContainerId, data, activeCohorts);
    });

    legendEl.appendChild(item);
  }
}
