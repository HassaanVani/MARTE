import type { SolveParams } from "../types";

interface Props {
  params: SolveParams;
  onChange: (params: SolveParams) => void;
}

function ParamInput({
  label,
  unit,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-text-dim flex items-baseline justify-between text-xs">
        <span>{label}</span>
        <span className="text-text-dim">{unit}</span>
      </label>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      />
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}

export function ParameterPanel({ params, onChange }: Props) {
  const update = (key: keyof SolveParams, value: number) => {
    onChange({ ...params, [key]: value });
  };

  return (
    <div className="flex flex-col gap-3 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Parameters
      </h2>
      <ParamInput
        label="Departure"
        unit="yr"
        value={params.t0_years}
        min={0}
        max={5}
        step={0.1}
        onChange={(v) => update("t0_years", v)}
      />
      <ParamInput
        label="Arrival"
        unit="yr"
        value={params.tf_years}
        min={0.5}
        max={10}
        step={0.1}
        onChange={(v) => update("tf_years", v)}
      />
      <ParamInput
        label="Proper time τ"
        unit="yr"
        value={params.proper_time_years}
        min={0.1}
        max={Math.max(params.tf_years - params.t0_years - 0.01, 0.1)}
        step={0.1}
        onChange={(v) => update("proper_time_years", v)}
      />
      <ParamInput
        label="Mass"
        unit="kg"
        value={params.mass_kg}
        min={1}
        max={100000}
        step={100}
        onChange={(v) => update("mass_kg", v)}
      />
    </div>
  );
}
