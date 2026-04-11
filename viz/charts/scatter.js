import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

const COLORS = {
  dormant_reactivated: "#e05c2a",
  consistently_active: "#3a86ff",
  new_surger:          "#8ac926",
};

const LABELS = {
  dormant_reactivated: "Dormant → Reactivated",
  consistently_active: "Consistently Active",
  new_surger:          "New Surger",
};

/**
 * Scatter plot: account age (years before 2022) vs. surge magnitude.
 * Dot size ∝ lifetime commits. Click/brush to populate detail table.
 *
 * @param {string} containerId
 * @param {Array}  data         — scatter_data.json
 */
export function renderScatter(containerId, data) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  // Size scale: sqrt of lifetime commits, capped
  const maxLifetime = Math.max(...data.map(d => d.lifetime_commits));

  const plot = Plot.plot({
    width: container.clientWidth || 900,
    height: 420,
    marginLeft: 65,
    marginRight: 20,
    marginBottom: 45,
    style: { background: "transparent", color: "#e6edf3", fontSize: "12px" },
    x: {
      label: "Account age before 2022 (years)",
      grid: true,
      domain: [0, 25],
    },
    y: {
      label: "Surge magnitude (post-peak − pre-peak, commits/yr)",
      grid: true,
      tickFormat: d => d >= 1000 ? `${(d/1000).toFixed(0)}k` : d,
    },
    color: {
      domain: Object.keys(COLORS),
      range: Object.values(COLORS),
    },
    r: { range: [2, 12] },
    marks: [
      Plot.dot(data, {
        x: "account_age",
        y: "surge_magnitude",
        fill: "cohort",
        r: d => Math.sqrt(d.lifetime_commits / maxLifetime) * 12 + 2,
        fillOpacity: 0.6,
        stroke: "cohort",
        strokeOpacity: 0.8,
        strokeWidth: 0.5,
        tip: true,
        title: d =>
          `${d.login}\nJoined: ${d.account_year}\nSurge: ${d.surge_magnitude > 1000
            ? (d.surge_magnitude/1000).toFixed(1)+"k"
            : Math.round(d.surge_magnitude)} commits/yr\nInflection: ${d.inflection_year ?? "—"}\nRatio: ${d.surge_ratio}×`,
      }),

      // Trend line per cohort (only dormant and new_surger)
      Plot.linearRegressionY(
        data.filter(d => d.cohort === "dormant_reactivated"),
        {
          x: "account_age",
          y: "surge_magnitude",
          stroke: COLORS.dormant_reactivated,
          strokeDasharray: "4,3",
          strokeOpacity: 0.7,
        }
      ),
    ],
  });

  // Wire up click → table
  plot.addEventListener("click", (event) => {
    const point = plot.value;
    if (!point) return;
    populateScatterTable([point]);
  });

  container.appendChild(plot);
}


function populateScatterTable(points) {
  const container = document.getElementById("scatter-table-container");
  const tbody = document.querySelector("#scatter-table tbody");

  container.hidden = false;
  tbody.innerHTML = "";

  for (const d of points) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><a href="https://github.com/${d.login}" target="_blank" rel="noopener">${d.login}</a></td>
      <td>${d.account_year}</td>
      <td style="color:${COLORS[d.cohort] ?? '#aaa'}">${LABELS[d.cohort] ?? d.cohort}</td>
      <td>${d.surge_ratio}×</td>
      <td>${d.inflection_year ?? "—"}</td>
    `;
    tbody.appendChild(tr);
  }
}
