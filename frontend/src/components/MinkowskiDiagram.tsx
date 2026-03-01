import { useCallback, useMemo, useRef } from "react";
import Plot from "react-plotly.js";
import type { EarthData, InterpolatedState, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
  interpolated: InterpolatedState | null;
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

export function MinkowskiDiagram({ worldline, earth, interpolated }: Props) {
  const lastUpdateRef = useRef(0);

  // Compute ship x-displacement for the indicator
  const depX = worldline.positions_au[0]![0]!;
  const depY = worldline.positions_au[0]![1]!;

  const computeShipX = useCallback(
    (pos: number[]) => {
      const dx = pos[0]! - depX;
      const dy = pos[1]! - depY;
      return Math.sqrt(dx * dx + dy * dy) * Math.sign(dx || dy || 1);
    },
    [depX, depY],
  );

  const traces = useMemo(() => {
    const shipX = worldline.positions_au.map(computeShipX);
    const shipCtLy = worldline.coord_times_years;

    const earthX = earth.trajectory_positions_au.map((p) => {
      const dx = p[0]! - depX;
      const dy = p[1]! - depY;
      return Math.sqrt(dx * dx + dy * dy) * Math.sign(dx || dy || 1);
    });
    const earthCt = earth.trajectory_times_years;

    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;
    const xMax = Math.max(...shipX.map(Math.abs), 2);
    const coneRange = Math.max(tMax, xMax) * 1.2;

    const result: Plotly.Data[] = [
      {
        x: [-coneRange, 0, coneRange],
        y: [coneRange, 0, coneRange],
        mode: "lines",
        line: { color: "#fbbf24", width: 1, dash: "dash" },
        name: "Light cone",
        showlegend: true,
      },
      {
        x: earthX,
        y: earthCt,
        mode: "lines",
        line: { color: "#3b82f6", width: 2 },
        name: "Earth",
      },
      {
        x: shipX,
        y: shipCtLy,
        mode: "lines+markers",
        line: { color: "#ef4444", width: 2 },
        marker: { size: 6, color: "#ef4444" },
        name: "Ship",
      },
    ];

    // Add indicator trace (will be updated)
    if (interpolated) {
      const ix = computeShipX(interpolated.positionAU);
      result.push({
        x: [ix],
        y: [interpolated.coordTime],
        mode: "markers",
        marker: { size: 12, color: "#f59e0b", symbol: "circle" },
        name: "Current",
        showlegend: false,
      });
    }

    return result;
  }, [worldline, earth, interpolated, computeShipX, depX, depY]);

  // Throttle re-renders to ~10fps for Plotly performance
  const now = performance.now();
  const shouldUpdate = now - lastUpdateRef.current > 100;
  if (shouldUpdate) lastUpdateRef.current = now;

  // Horizontal dashed line at current ct
  const shapes: Partial<Plotly.Shape>[] = [];
  if (interpolated && shouldUpdate) {
    const tMax = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;
    const xMax = 3;
    shapes.push({
      type: "line",
      x0: -xMax,
      x1: xMax,
      y0: interpolated.coordTime,
      y1: interpolated.coordTime,
      line: { color: "#f59e0b", width: 1, dash: "dash" },
    });
    // Vertical reference line
    shapes.push({
      type: "line",
      x0: computeShipX(interpolated.positionAU),
      x1: computeShipX(interpolated.positionAU),
      y0: 0,
      y1: tMax,
      line: { color: "#f59e0b33", width: 1, dash: "dot" },
    });
  }

  return (
    <Plot
      data={traces}
      layout={{
        ...LAYOUT_BASE,
        title: { text: "MINKOWSKI DIAGRAM", font: { size: 11, color: "#f59e0b" } },
        shapes,
      }}
      config={{ responsive: true, displayModeBar: false }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
    />
  );
}
