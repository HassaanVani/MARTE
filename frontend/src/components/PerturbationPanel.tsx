import type { PerturbationData } from "../types";

interface Props {
  perturbation: PerturbationData;
}

const G = 9.80665;
const AU = 1.496e11;

export function PerturbationPanel({ perturbation }: Props) {
  const rows: [string, string][] = [
    ["SUN  a_max", `${(perturbation.max_accel_sun_m_s2 / G).toExponential(2)} g`],
    ["JUP  a_max", `${(perturbation.max_accel_jupiter_m_s2 / G).toExponential(2)} g`],
    ["SAT  a_max", `${(perturbation.max_accel_saturn_m_s2 / G).toExponential(2)} g`],
    ["SUN  \u0394v", `${perturbation.total_delta_v_sun_m_s.toFixed(1)} m/s`],
    ["JUP  \u0394v", `${perturbation.total_delta_v_jupiter_m_s.toFixed(4)} m/s`],
    ["SAT  \u0394v", `${perturbation.total_delta_v_saturn_m_s.toFixed(4)} m/s`],
    ["SUN  d_min", `${(perturbation.closest_approach_sun_m / AU).toFixed(3)} AU`],
    ["JUP  d_min", `${(perturbation.closest_approach_jupiter_m / AU).toFixed(2)} AU`],
    ["SAT  d_min", `${(perturbation.closest_approach_saturn_m / AU).toFixed(2)} AU`],
  ];

  return (
    <div className="flex flex-col gap-1 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Perturbation
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
