import type { SolveResponse } from "../types";

interface Props {
  response: SolveResponse | null;
}

const GLOBAL_ANNUAL_ENERGY = 6e20; // Joules (approximate)

export function EnergyDisplay({ response }: Props) {
  const sol = response?.solution;
  if (!sol) return null;

  const energy = sol.energy_joules;
  const fraction = energy / GLOBAL_ANNUAL_ENERGY;
  const pct = fraction * 100;

  let barColor = "bg-green";
  if (pct > 50) barColor = "bg-red";
  else if (pct > 1) barColor = "bg-amber";

  const barWidth = Math.min(pct, 100);

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Energy Budget
      </h2>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">E_kinetic</span>
        <span className="text-xs tabular-nums">
          {energy.toExponential(3)} J
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">% global annual</span>
        <span className="text-xs tabular-nums">
          {pct < 0.01 ? pct.toExponential(1) : pct.toFixed(2)}%
        </span>
      </div>
      <div className="bg-surface h-2 w-full border border-border">
        <div
          className={`h-full ${barColor}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>
      <p className="text-text-dim text-[10px]">
        ref: ~6×10²⁰ J global annual energy
      </p>
    </div>
  );
}
