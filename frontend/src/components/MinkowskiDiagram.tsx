import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { EarthData, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
}

const LAYOUT_BASE: Partial<Plotly.Layout> = {
  paper_bgcolor: "#09090b",
  plot_bgcolor: "#09090b",
  font: { family: "JetBrains Mono, monospace", size: 11, color: "#e4e4e7" },
  margin: { l: 60, r: 20, t: 30, b: 50 },
  xaxis: {
    title: { text: "x (AU)" },
    gridcolor: "#27272a",
    zerolinecolor: "#3f3f46",
    color: "#a1a1aa",
  },
  yaxis: {
    title: { text: "ct (light-years)" },
    gridcolor: "#27272a",
    zerolinecolor: "#3f3f46",
    color: "#a1a1aa",
  },
  showlegend: true,
  legend: { x: 0.02, y: 0.98, font: { size: 10 }, bgcolor: "transparent" },
};

export function MinkowskiDiagram({ worldline, earth }: Props) {
  const traces = useMemo(() => {
    // Ship worldline: x-displacement in AU vs ct in light-years
    // For Minkowski diagram, use displacement along trajectory direction from departure
    const depX = worldline.positions_au[0]![0]!;
    const depY = worldline.positions_au[0]![1]!;

    // Project positions onto displacement axis relative to departure
    const shipX = worldline.positions_au.map((p) => {
      const dx = p[0]! - depX;
      const dy = p[1]! - depY;
      return Math.sqrt(dx * dx + dy * dy) * Math.sign(dx || dy || 1);
    });
    // ct in light-years = t in years (since c = 1 ly/yr)
    const shipCtLy = worldline.coord_times_years;

    // Earth worldline projected similarly
    const earthX = earth.trajectory_positions_au.map((p) => {
      const dx = p[0]! - depX;
      const dy = p[1]! - depY;
      return Math.sqrt(dx * dx + dy * dy) * Math.sign(dx || dy || 1);
    });
    const earthCt = earth.trajectory_times_years;

    // Light cones from departure
    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;
    const xMax = Math.max(...shipX.map(Math.abs), 2);
    const coneRange = Math.max(tMax, xMax) * 1.2;

    const result: Plotly.Data[] = [
      // Light cone (future)
      {
        x: [-coneRange, 0, coneRange],
        y: [coneRange, 0, coneRange],
        mode: "lines",
        line: { color: "#fbbf24", width: 1, dash: "dash" },
        name: "Light cone",
        showlegend: true,
      },
      // Earth worldline
      {
        x: earthX,
        y: earthCt,
        mode: "lines",
        line: { color: "#3b82f6", width: 2 },
        name: "Earth",
      },
      // Ship worldline
      {
        x: shipX,
        y: shipCtLy,
        mode: "lines+markers",
        line: { color: "#ef4444", width: 2 },
        marker: { size: 6, color: "#ef4444" },
        name: "Ship",
      },
    ];

    return result;
  }, [worldline, earth]);

  return (
    <Plot
      data={traces}
      layout={{
        ...LAYOUT_BASE,
        title: { text: "MINKOWSKI DIAGRAM", font: { size: 11, color: "#f59e0b" } },
      }}
      config={{ responsive: true, displayModeBar: false }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
    />
  );
}
