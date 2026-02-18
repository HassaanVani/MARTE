import type { SolveResponse } from "../types";

interface Props {
  response: SolveResponse | null;
  loading: boolean;
}

function Row({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-text-dim text-xs">{label}</span>
      <span className="text-text text-xs tabular-nums">
        {value}
        {unit && <span className="text-text-dim ml-1">{unit}</span>}
      </span>
    </div>
  );
}

function formatSci(n: number, digits = 4): string {
  return n.toExponential(digits);
}

export function ResultsPanel({ response, loading }: Props) {
  const sol = response?.solution;

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Results
      </h2>
      {!sol && !loading && (
        <p className="text-text-dim text-xs">No solution</p>
      )}
      {loading && <p className="text-text-dim text-xs">Computing...</p>}
      {sol && (
        <>
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 ${sol.converged ? "bg-green" : "bg-red"}`}
            />
            <span className="text-xs">
              {sol.converged ? "CONVERGED" : "NOT CONVERGED"}
            </span>
          </div>
          <Row label="β" value={sol.beta.toFixed(6)} />
          <Row label="γ" value={sol.gamma.toFixed(6)} />
          <Row label="v" value={formatSci(sol.speed_m_s)} unit="m/s" />
          <Row
            label="t_turn"
            value={sol.turnaround_time_years.toFixed(4)}
            unit="yr"
          />
          <Row
            label="τ_total"
            value={sol.total_proper_time_years.toFixed(4)}
            unit="yr"
          />
          <Row label="residual" value={formatSci(sol.residual, 2)} />
        </>
      )}
    </div>
  );
}
