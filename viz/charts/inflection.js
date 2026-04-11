import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";

/**
 * Bar chart: distribution of inflection years among surging users.
 *
 * @param {string} containerId
 * @param {Array}  data  — inflection_histogram.json [{year, count}]
 */
export function renderInflection(containerId, data) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  const maxCount = Math.max(...data.map(d => d.count));

  const plot = Plot.plot({
    width: container.clientWidth || 900,
    height: 280,
    marginLeft: 60,
    marginRight: 20,
    marginBottom: 45,
    style: { background: "transparent", color: "#e6edf3", fontSize: "12px" },
    x: {
      label: "Inflection year",
      tickFormat: d => String(d),
      grid: false,
    },
    y: {
      label: "Users",
      grid: true,
    },
    marks: [
      Plot.barY(data, {
        x: "year",
        y: "count",
        fill: d => {
          // Gradient-ish: highlight 2022–2024 as the AI era
          if (d.year >= 2022 && d.year <= 2024) return "#e05c2a";
          if (d.year >= 2019 && d.year < 2022) return "#3a86ff";
          return "#aaa";
        },
        tip: true,
        title: d => `${d.year}: ${d.count.toLocaleString()} users`,
      }),

      // Annotation for Copilot GA
      Plot.ruleX([2022], { stroke: "#fff", strokeDasharray: "4,3", strokeWidth: 1 }),
      Plot.text([{ year: 2022, label: "Copilot GA →" }], {
        x: "year",
        y: maxCount * 0.92,
        text: "label",
        fill: "#8b949e",
        fontSize: 10,
        dx: -4,
        textAnchor: "end",
      }),
    ],
  });

  container.appendChild(plot);
}
