import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
}

const LAYOUT_BASE: Partial<Plotly.Layout> = {
  paper_bgcolor: "#09090b",
  plot_bgcolor: "#09090b",
  font: { family: "JetBrains Mono, monospace", size: 11, color: "#e4e4e7" },
  margin: { l: 60, r: 20, t: 30, b: 50 },
  xaxis: {
    title: { text: "Coordinate time t (years)" },
    gridcolor: "#27272a",
    zerolinecolor: "#3f3f46",
    color: "#a1a1aa",
  },
  yaxis: {
    title: { text: "Proper time τ (years)" },
    gridcolor: "#27272a",
    zerolinecolor: "#3f3f46",
    color: "#a1a1aa",
  },
  showlegend: true,
  legend: { x: 0.02, y: 0.98, font: { size: 10 }, bgcolor: "transparent" },
};

export function ProperTimeCurve({ worldline }: Props) {
  const traces = useMemo(() => {
    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;

    const result: Plotly.Data[] = [
      // Reference line τ = t (no dilation)
      {
        x: [0, tMax],
        y: [0, tMax],
        mode: "lines",
        line: { color: "#71717a", width: 1, dash: "dash" },
        name: "τ = t (no dilation)",
      },
      // Ship proper time curve
      {
        x: worldline.coord_times_years,
        y: worldline.proper_times_years,
        mode: "lines+markers",
        line: { color: "#ef4444", width: 2 },
        marker: { size: 6, color: "#ef4444" },
        name: "Ship τ(t)",
      },
    ];

    return result;
  }, [worldline]);

  // Compute slope annotation (dτ/dt = 1/γ)
  const gamma =
    worldline.coord_times_years.length >= 2 && worldline.proper_times_years.length >= 2
      ? (worldline.coord_times_years[1]! - worldline.coord_times_years[0]!) /
        (worldline.proper_times_years[1]! - worldline.proper_times_years[0]!)
      : null;

  const annotations: Partial<Plotly.Annotations>[] = gamma
    ? [
        {
          x: worldline.coord_times_years[1]!,
          y: worldline.proper_times_years[1]!,
          text: `dτ/dt = 1/γ ≈ ${(1 / gamma).toFixed(4)}`,
          showarrow: true,
          arrowhead: 0,
          ax: 40,
          ay: -30,
          font: { size: 10, color: "#f59e0b" },
          arrowcolor: "#f59e0b",
        },
      ]
    : [];

  return (
    <Plot
      data={traces}
      layout={{
        ...LAYOUT_BASE,
        title: { text: "PROPER TIME CURVE", font: { size: 11, color: "#f59e0b" } },
        annotations,
      }}
      config={{ responsive: true, displayModeBar: false }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
    />
  );
}
