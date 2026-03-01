import { useMemo, useRef } from "react";
import Plot from "react-plotly.js";
import type { InterpolatedState, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  interpolated: InterpolatedState | null;
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

export function ProperTimeCurve({ worldline, interpolated }: Props) {
  const lastUpdateRef = useRef(0);

  const traces = useMemo(() => {
    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;

    const result: Plotly.Data[] = [
      {
        x: [0, tMax],
        y: [0, tMax],
        mode: "lines",
        line: { color: "#71717a", width: 1, dash: "dash" },
        name: "τ = t (no dilation)",
      },
      {
        x: worldline.coord_times_years,
        y: worldline.proper_times_years,
        mode: "lines+markers",
        line: { color: "#ef4444", width: 2 },
        marker: { size: 6, color: "#ef4444" },
        name: "Ship τ(t)",
      },
    ];

    // Indicator dot
    if (interpolated) {
      result.push({
        x: [interpolated.coordTime],
        y: [interpolated.properTime],
        mode: "markers",
        marker: { size: 12, color: "#f59e0b", symbol: "circle" },
        name: "Current",
        showlegend: false,
      });
    }

    return result;
  }, [worldline, interpolated]);

  // Slope annotation
  const len = worldline.coord_times_years.length;
  const midIdx = Math.max(1, Math.floor(len / 2));
  const prevIdx = midIdx - 1;
  const dtCoord = worldline.coord_times_years[midIdx]! - worldline.coord_times_years[prevIdx]!;
  const dtProper = worldline.proper_times_years[midIdx]! - worldline.proper_times_years[prevIdx]!;
  const gamma = dtCoord > 0 && dtProper > 0 ? dtCoord / dtProper : null;

  const annotations: Partial<Plotly.Annotations>[] = gamma
    ? [
        {
          x: worldline.coord_times_years[midIdx]!,
          y: worldline.proper_times_years[midIdx]!,
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

  // Throttle shapes to ~10fps
  const now = performance.now();
  const shouldUpdate = now - lastUpdateRef.current > 100;
  if (shouldUpdate) lastUpdateRef.current = now;

  // Vertical dashed line at current coord time
  const shapes: Partial<Plotly.Shape>[] = [];
  if (interpolated && shouldUpdate) {
    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;
    shapes.push({
      type: "line",
      x0: interpolated.coordTime,
      x1: interpolated.coordTime,
      y0: 0,
      y1: tMax,
      line: { color: "#f59e0b", width: 1, dash: "dash" },
    });
  }

  return (
    <Plot
      data={traces}
      layout={{
        ...LAYOUT_BASE,
        title: { text: "PROPER TIME CURVE", font: { size: 11, color: "#f59e0b" } },
        annotations,
        shapes,
      }}
      config={{ responsive: true, displayModeBar: false }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
    />
  );
}
