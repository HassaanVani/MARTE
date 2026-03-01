import type { ConvergenceDiagnostics } from "../types";

interface Props {
  convergence: ConvergenceDiagnostics | null;
}

export function ResidualMonitor({ convergence }: Props) {
  if (!convergence) return null;

  const rows: [string, string][] = [
    ["STATUS", convergence.converged ? "CONVERGED" : "NOT CONVERGED"],
    ["RESIDUAL", convergence.residual_norm.toExponential(3)],
    ["POS ERR", `${convergence.position_error_m.toExponential(2)} m`],
    ["TAU ERR", `${convergence.proper_time_error_s.toExponential(2)} s`],
  ];

  if (convergence.n_function_evals != null) {
    rows.push(["F EVALS", String(convergence.n_function_evals)]);
  }
  if (convergence.solver_message) {
    rows.push(["MESSAGE", convergence.solver_message]);
  }

  return (
    <div className="flex flex-col gap-1 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Convergence
      </h2>
      <div className="bg-bg border-border border p-2 font-mono text-[11px] leading-relaxed">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-2">
            <span className="text-text-dim">{label}</span>
            <span className="text-amber truncate text-right">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
