import type { FuelBudgetData } from "../types";

interface Props {
  fuelBudget: FuelBudgetData | null;
}

export function FuelBudgetPanel({ fuelBudget }: Props) {
  if (!fuelBudget) return null;

  const { mass_ratio, fuel_mass_fraction, fuel_mass_kg, total_rapidity_change, total_energy_joules } = fuelBudget;
  const pct = fuel_mass_fraction * 100;

  let barColor = "bg-green";
  if (pct > 90) barColor = "bg-red";
  else if (pct > 50) barColor = "bg-amber";

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Fuel Budget
      </h2>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">Mass ratio m₀/m_f</span>
        <span className="text-xs tabular-nums">
          {mass_ratio < 1000 ? mass_ratio.toFixed(2) : mass_ratio.toExponential(2)}
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">Fuel fraction</span>
        <span className="text-xs tabular-nums">{pct.toFixed(1)}%</span>
      </div>
      <div className="bg-surface h-2 w-full border border-border">
        <div
          className={`h-full ${barColor}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">Fuel mass</span>
        <span className="text-xs tabular-nums">
          {fuel_mass_kg < 1e6 ? fuel_mass_kg.toFixed(1) : fuel_mass_kg.toExponential(3)} kg
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">Total rapidity</span>
        <span className="text-xs tabular-nums">
          {total_rapidity_change.toFixed(4)}
        </span>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-text-dim text-xs">E_fuel</span>
        <span className="text-xs tabular-nums">
          {total_energy_joules.toExponential(3)} J
        </span>
      </div>
    </div>
  );
}
