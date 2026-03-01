import type { GRDiagnosticsData } from "../types";

interface Props {
  diagnostics: GRDiagnosticsData;
}

function severityColor(deltaS: number): string {
  const abs = Math.abs(deltaS);
  if (abs < 1) return "text-green";
  if (abs < 100) return "text-amber";
  return "text-red";
}

export function GRDiagnosticsPanel({ diagnostics }: Props) {
  const dtColor = severityColor(diagnostics.delta_tau_s);

  const rows: [string, string, string?][] = [
    ["SR \u03c4", `${diagnostics.sr_proper_time_years.toFixed(6)} yr`],
    ["GR \u03c4", `${diagnostics.gr_proper_time_years.toFixed(6)} yr`],
    ["\u0394\u03c4", `${diagnostics.delta_tau_s.toFixed(4)} s`, dtColor],
    ["REL CORR", diagnostics.relative_correction.toExponential(3)],
    ["MIN r\u2609", `${diagnostics.min_distance_from_sun_au.toFixed(3)} AU`],
    ["MAX DILATION", diagnostics.max_gravitational_dilation.toExponential(3)],
  ];

  return (
    <div className="flex flex-col gap-1 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        GR Corrections
      </h2>
      <div className="bg-bg border-border border p-2 font-mono text-[11px] leading-relaxed">
        {rows.map(([label, value, color]) => (
          <div key={label} className="flex justify-between gap-2">
            <span className="text-text-dim">{label}</span>
            <span className={`${color ?? "text-amber"} truncate text-right`}>
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
