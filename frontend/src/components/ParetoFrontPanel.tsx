import { useState } from "react";
import { computePareto } from "../api";
import type { ParetoResult, SolveParams } from "../types";

interface Props {
  params: SolveParams;
  onResult: (result: ParetoResult) => void;
  result: ParetoResult | null;
}

export function ParetoFrontPanel({ params, onResult, result }: Props) {
  const [loading, setLoading] = useState(false);
  const [nPoints, setNPoints] = useState(50);

  const handleCompute = async () => {
    setLoading(true);
    try {
      const res = await computePareto({
        t0_years: params.t0_years,
        tf_years: params.tf_years,
        mass_kg: params.mass_kg,
        trajectory_model: params.trajectory_model,
        proper_acceleration_g: params.proper_acceleration_g,
        target: params.target,
        n_points: nPoints,
        earth_model: params.earth_model,
      });
      onResult(res);
    } catch {
      // failed
    } finally {
      setLoading(false);
    }
  };

  // Simple ASCII-style chart
  const chart = result && result.points.length > 0 ? (() => {
    const pts = result.points;
    const maxE = Math.max(...pts.map((p) => p.energy_joules));
    return pts.map((p) => ({
      tau: p.proper_time_years,
      energy: p.energy_joules,
      beta: p.peak_beta,
      barWidth: maxE > 0 ? (p.energy_joules / maxE) * 100 : 0,
    }));
  })() : null;

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Pareto Front
      </h2>
      <div className="flex gap-2 items-end">
        <div className="flex flex-col flex-1">
          <span className="text-text-dim text-[10px]">Points</span>
          <input
            type="number"
            value={nPoints}
            min={5}
            max={100}
            onChange={(e) => setNPoints(+e.target.value)}
            className="w-full"
          />
        </div>
        <button
          onClick={handleCompute}
          disabled={loading}
          className="bg-amber text-bg px-3 py-1.5 text-xs font-bold uppercase tracking-widest disabled:opacity-50"
        >
          {loading ? "..." : "Compute"}
        </button>
      </div>

      {chart && (
        <div className="flex flex-col gap-0.5 mt-2">
          <div className="text-text-dim text-[10px] flex justify-between">
            <span>Proper time (yr)</span>
            <span>Energy (J)</span>
          </div>
          {chart.map((row, i) => (
            <div key={i} className="flex items-center gap-2 text-[10px]">
              <span className="text-text-dim w-10 text-right shrink-0">
                {row.tau.toFixed(2)}
              </span>
              <div className="flex-1 h-3 bg-surface relative">
                <div
                  className="h-full"
                  style={{
                    width: `${row.barWidth}%`,
                    backgroundColor: `hsl(${(1 - row.beta) * 120}, 70%, 50%)`,
                  }}
                />
              </div>
              <span className="text-text-dim w-16 text-right shrink-0">
                {row.energy.toExponential(1)}
              </span>
            </div>
          ))}
          <div className="text-text-dim text-[10px] mt-1">
            {result!.points.length} Pareto-optimal points
          </div>
        </div>
      )}
    </div>
  );
}
