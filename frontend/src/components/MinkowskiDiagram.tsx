import { useCallback, useMemo, useRef } from "react";
import Plot from "react-plotly.js";
import type { BranchData, EarthData, InterpolatedState, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  earth: EarthData;
  interpolated: InterpolatedState | null;
  branches?: BranchData[] | null;
  selectedBranch?: number;
  onArrivalTimeChange?: (tf_years: number) => void;
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
    title: { text: "t (years)" },
    gridcolor: "#27272a",
    zerolinecolor: "#3f3f46",
    color: "#a1a1aa",
  },
  showlegend: true,
  legend: { x: 0.02, y: 0.98, font: { size: 10 }, bgcolor: "transparent" },
};

export function MinkowskiDiagram({
  worldline,
  earth,
  interpolated,
  branches,
  selectedBranch = 0,
  onArrivalTimeChange,
}: Props) {
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

    const xMax = Math.max(...shipX.map(Math.abs), 2) * 1.2;

    // c ≈ 63,241 AU/year. Light cone: t = |x| / c.
    // At trajectory scales (~AU) the cone is nearly vertical.
    const C_AU_PER_YEAR = 63241.077;
    const lcT = xMax / C_AU_PER_YEAR;  // time for light to cross the spatial range

    const result: Plotly.Data[] = [
      {
        x: [-xMax, 0, xMax],
        y: [lcT, 0, lcT],
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
    ];

    // Non-selected branch traces (dimmed red)
    if (branches && branches.length > 1) {
      for (let i = 0; i < branches.length; i++) {
        if (i === selectedBranch) continue;
        const bwl = branches[i]!.worldline;
        const bShipX = bwl.positions_au.map(computeShipX);
        result.push({
          x: bShipX,
          y: bwl.coord_times_years,
          mode: "lines",
          line: { color: "#ef4444", width: 1, dash: "dot" },
          opacity: 0.3,
          name: `Branch ${String.fromCharCode(65 + i)}`,
          showlegend: true,
        });
      }
    }

    // Active ship worldline
    result.push({
      x: shipX,
      y: shipCtLy,
      mode: "lines+markers",
      line: { color: "#ef4444", width: 2 },
      marker: { size: 6, color: "#ef4444" },
      name: "Ship",
    });

    // Current position indicator
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

    // Arrival event diamond marker
    const arrivalT = worldline.coord_times_years[worldline.coord_times_years.length - 1]!;
    const arrivalX = shipX[shipX.length - 1]!;
    result.push({
      x: [arrivalX],
      y: [arrivalT],
      mode: "markers",
      marker: { size: 10, color: "#f59e0b", symbol: "diamond", opacity: 0.5 },
      name: "Arrival",
      showlegend: false,
    });

    return result;
  }, [worldline, earth, interpolated, computeShipX, depX, depY, branches, selectedBranch]);

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

  const handleClick = useCallback(
    (event: Plotly.PlotMouseEvent) => {
      if (!onArrivalTimeChange || !event.points || event.points.length === 0) return;
      const point = event.points[0];
      if (point && typeof point.y === "number" && point.y > 0) {
        onArrivalTimeChange(point.y);
      }
    },
    [onArrivalTimeChange],
  );

  return (
    <Plot
      data={traces}
      layout={{
        ...LAYOUT_BASE,
        title: { text: "MINKOWSKI DIAGRAM", font: { size: 11, color: "#f59e0b" } },
        shapes,
        clickmode: onArrivalTimeChange ? "event" : "none",
      }}
      config={{ responsive: true, displayModeBar: false }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
      onClick={onArrivalTimeChange ? handleClick : undefined}
    />
  );
}
