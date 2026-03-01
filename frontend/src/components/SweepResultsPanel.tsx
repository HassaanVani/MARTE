import { useMemo } from "react";
import type { Sweep1DResult, Sweep2DResult } from "../types";

interface Props {
  sweep1D: Sweep1DResult | null;
  sweep2D: Sweep2DResult | null;
  onSelectPoint?: (params: Record<string, number>) => void;
}

export function SweepResultsPanel({ sweep1D, sweep2D }: Props) {
  // 1D: simple table/chart representation
  const chart1D = useMemo(() => {
    if (!sweep1D) return null;
    const converged = sweep1D.points.filter((p) => p.converged);
    if (converged.length === 0) return null;

    const maxEnergy = Math.max(...converged.map((p) => p.energy ?? 0));
    return converged.map((p) => ({
      param: p.param_value ?? 0,
      energy: p.energy ?? 0,
      beta: p.peak_beta ?? 0,
      tau: p.proper_time_years ?? 0,
      barWidth: maxEnergy > 0 ? ((p.energy ?? 0) / maxEnergy) * 100 : 0,
    }));
  }, [sweep1D]);

  // 2D: grid representation
  const grid2D = useMemo(() => {
    if (!sweep2D) return null;
    const { x_steps, y_steps, points } = sweep2D;
    const rows: typeof points[number][][] = [];
    for (let y = 0; y < y_steps; y++) {
      rows.push(points.slice(y * x_steps, (y + 1) * x_steps));
    }
    return rows;
  }, [sweep2D]);

  if (!sweep1D && !sweep2D) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="text-text-dim text-xs">Run a sweep to see results</p>
      </div>
    );
  }

  if (chart1D && sweep1D) {
    return (
      <div className="flex flex-col gap-2 p-4 overflow-auto">
        <h3 className="text-amber text-xs font-bold uppercase">
          {sweep1D.swept_param} Sweep
        </h3>
        <div className="flex flex-col gap-0.5">
          {chart1D.map((row, i) => (
            <div key={i} className="flex items-center gap-2 text-[10px]">
              <span className="text-text-dim w-12 text-right shrink-0">
                {row.param.toFixed(2)}
              </span>
              <div className="flex-1 h-3 bg-surface relative">
                <div
                  className="h-full bg-amber/60"
                  style={{ width: `${row.barWidth}%` }}
                />
              </div>
              <span className="text-text-dim w-16 text-right shrink-0">
                {row.energy.toExponential(1)} J
              </span>
            </div>
          ))}
        </div>
        <div className="text-text-dim text-[10px] mt-1">
          {chart1D.length} / {sweep1D.points.length} converged
        </div>
      </div>
    );
  }

  if (grid2D && sweep2D) {
    const maxE = Math.max(
      ...sweep2D.points.filter((p) => p.converged).map((p) => p.energy ?? 0),
    );
    return (
      <div className="flex flex-col gap-2 p-4 overflow-auto">
        <h3 className="text-amber text-xs font-bold uppercase">
          {sweep2D.x_param} vs {sweep2D.y_param}
        </h3>
        <div className="grid gap-px" style={{ gridTemplateColumns: `repeat(${sweep2D.x_steps}, 1fr)` }}>
          {grid2D.flat().map((pt, i) => {
            const intensity = pt.converged && pt.energy != null && maxE > 0
              ? Math.round((pt.energy / maxE) * 255)
              : 0;
            const bg = pt.converged
              ? `rgb(${intensity}, ${Math.round(intensity * 0.6)}, 0)`
              : "#1a1a1a";
            return (
              <div
                key={i}
                className="aspect-square"
                style={{ backgroundColor: bg }}
                title={pt.converged ? `E=${(pt.energy ?? 0).toExponential(1)} J` : "failed"}
              />
            );
          })}
        </div>
        <div className="text-text-dim text-[10px]">
          {sweep2D.points.filter((p) => p.converged).length} / {sweep2D.points.length} converged
        </div>
      </div>
    );
  }

  return null;
}
