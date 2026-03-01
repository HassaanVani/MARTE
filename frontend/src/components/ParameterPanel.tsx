import type { SolveParams } from "../types";

interface Props {
  params: SolveParams;
  onChange: (params: SolveParams) => void;
}

interface Preset {
  name: string;
  description: string;
  params: SolveParams;
}

const DEFAULT_EXTRAS = {
  exhaust_velocity_c: null as number | null,
  elliptical_orbit: false,
  find_all_branches: false,
  acceleration_profile: "step",
  ramp_fraction: 0.1,
  max_acceleration_g: null as number | null,
  earth_model: null as string | null,
  gr_corrections: false,
  compute_perturbation: false,
  target: "earth",
};

const PRESETS: Preset[] = [
  {
    name: "Twin Paradox",
    description: "Classic thought experiment — 2 yr trip, ship ages 1.5 yr",
    params: {
      t0_years: 0,
      tf_years: 2,
      proper_time_years: 1.5,
      mass_kg: 1000,
      trajectory_model: "constant_velocity",
      proper_acceleration_g: null,
      ...DEFAULT_EXTRAS,
    },
  },
  {
    name: "Time Dilation Express",
    description: "Extreme dilation — 5 yr trip, only 1 yr on ship clock",
    params: {
      t0_years: 0,
      tf_years: 5,
      proper_time_years: 1.0,
      mass_kg: 1000,
      trajectory_model: "constant_velocity",
      proper_acceleration_g: null,
      ...DEFAULT_EXTRAS,
    },
  },
  {
    name: "Slow Cruise",
    description: "Low speed — minimal time dilation, almost Newtonian",
    params: {
      t0_years: 0,
      tf_years: 4,
      proper_time_years: 3.9,
      mass_kg: 1000,
      trajectory_model: "constant_velocity",
      proper_acceleration_g: null,
      ...DEFAULT_EXTRAS,
    },
  },
  {
    name: "1g Brachistochrone",
    description: "Human-comfortable 1g acceleration, 10 yr roundtrip",
    params: {
      t0_years: 0,
      tf_years: 10,
      proper_time_years: 5,
      mass_kg: 10000,
      trajectory_model: "constant_acceleration",
      proper_acceleration_g: 1.0,
      ...DEFAULT_EXTRAS,
    },
  },
  {
    name: "High-g Sprint",
    description: "3g burn — brutal acceleration, extreme dilation",
    params: {
      t0_years: 0,
      tf_years: 8,
      proper_time_years: 2,
      mass_kg: 5000,
      trajectory_model: "constant_acceleration",
      proper_acceleration_g: 3.0,
      ...DEFAULT_EXTRAS,
    },
  },
  {
    name: "Mars Transfer",
    description: "Earth-to-Mars transfer — 1.5 yr trip at 1g",
    params: {
      t0_years: 0,
      tf_years: 1.5,
      proper_time_years: 1.2,
      mass_kg: 5000,
      trajectory_model: "constant_acceleration",
      proper_acceleration_g: 1.0,
      ...DEFAULT_EXTRAS,
      target: "mars",
    },
  },
  {
    name: "Venus Flyby",
    description: "Earth-to-Venus — 0.8 yr quick transfer",
    params: {
      t0_years: 0,
      tf_years: 0.8,
      proper_time_years: 0.6,
      mass_kg: 2000,
      trajectory_model: "constant_acceleration",
      proper_acceleration_g: 1.0,
      ...DEFAULT_EXTRAS,
      target: "venus",
    },
  },
  {
    name: "Jupiter Mission",
    description: "Earth-to-Jupiter — 6 yr deep space mission",
    params: {
      t0_years: 0,
      tf_years: 6,
      proper_time_years: 4,
      mass_kg: 10000,
      trajectory_model: "constant_acceleration",
      proper_acceleration_g: 1.0,
      ...DEFAULT_EXTRAS,
      target: "jupiter",
    },
  },
];

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

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="accent-amber"
      />
      <span className="text-text-dim">{label}</span>
    </label>
  );
}

export function ParameterPanel({ params, onChange }: Props) {
  const update = (key: keyof SolveParams, value: number) => {
    onChange({ ...params, [key]: value });
  };

  const isV2 = params.trajectory_model === "constant_acceleration";
  const fuelEnabled = params.exhaust_velocity_c !== null;

  return (
    <div className="flex flex-col gap-3 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Mission
      </h2>

      {/* Presets */}
      <div className="flex flex-col gap-1">
        <label className="text-text-dim text-[10px] tracking-wider uppercase">
          Quick Start
        </label>
        <div className="flex flex-col gap-1">
          {PRESETS.map((preset) => (
            <button
              key={preset.name}
              onClick={() => onChange(preset.params)}
              className="border-border hover:border-amber hover:text-amber group border px-2 py-1.5 text-left transition-colors"
            >
              <div className="text-xs font-bold">{preset.name}</div>
              <div className="text-text-dim group-hover:text-text-dim text-[10px]">
                {preset.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="border-border my-1 border-t" />

      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Custom
      </h2>

      {/* Target selector */}
      <div className="flex flex-col gap-1">
        <label className="text-text-dim text-xs">Target</label>
        <select
          value={params.target}
          onChange={(e) =>
            onChange({ ...params, target: e.target.value })
          }
          className="bg-surface text-text border-border border px-2 py-1 text-xs"
        >
          <option value="earth">Earth (round-trip)</option>
          <option value="mercury">Mercury</option>
          <option value="venus">Venus</option>
          <option value="mars">Mars</option>
          <option value="jupiter">Jupiter</option>
        </select>
      </div>

      {/* Model selector */}
      <div className="flex flex-col gap-1">
        <label className="text-text-dim text-xs">Physics Model</label>
        <select
          value={params.trajectory_model}
          onChange={(e) =>
            onChange({
              ...params,
              trajectory_model: e.target.value,
              proper_acceleration_g:
                e.target.value === "constant_acceleration"
                  ? params.proper_acceleration_g ?? 1.0
                  : null,
              find_all_branches:
                e.target.value === "constant_acceleration"
                  ? params.find_all_branches
                  : false,
            })
          }
          className="bg-surface text-text border-border border px-2 py-1 text-xs"
        >
          <option value="constant_velocity">Constant Velocity (v1)</option>
          <option value="constant_acceleration">Constant Acceleration (v2)</option>
        </select>
      </div>

      {isV2 && (
        <ParamInput
          label="Acceleration"
          unit="g"
          value={params.proper_acceleration_g ?? 1.0}
          min={0.1}
          max={10}
          step={0.1}
          onChange={(v) => onChange({ ...params, proper_acceleration_g: v })}
        />
      )}

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
        max={isV2 ? 20 : 10}
        step={0.1}
        onChange={(v) => update("tf_years", v)}
      />
      <ParamInput
        label="Ship proper time τ"
        unit="yr"
        value={params.proper_time_years}
        min={0.1}
        max={Math.max(params.tf_years - params.t0_years - 0.01, 0.1)}
        step={0.1}
        onChange={(v) => update("proper_time_years", v)}
      />
      <ParamInput
        label="Ship mass"
        unit="kg"
        value={params.mass_kg}
        min={1}
        max={100000}
        step={100}
        onChange={(v) => update("mass_kg", v)}
      />

      <div className="border-border my-1 border-t" />

      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Options
      </h2>

      {/* Earth Orbit Model */}
      <div className="flex flex-col gap-1">
        <label className="text-text-dim text-xs">Earth Orbit Model</label>
        <select
          value={params.earth_model ?? (params.elliptical_orbit ? "elliptical" : "circular")}
          onChange={(e) => {
            const val = e.target.value;
            onChange({
              ...params,
              earth_model: val === "circular" ? null : val,
              elliptical_orbit: val === "elliptical",
            });
          }}
          className="bg-surface text-text border-border border px-2 py-1 text-xs"
        >
          <option value="circular">Circular</option>
          <option value="elliptical">Elliptical (e=0.017)</option>
          <option value="ephemeris">JPL Horizons</option>
        </select>
      </div>

      <Checkbox
        label="GR corrections"
        checked={params.gr_corrections}
        onChange={(v) => onChange({ ...params, gr_corrections: v })}
      />

      <Checkbox
        label="Multi-body perturbation"
        checked={params.compute_perturbation}
        onChange={(v) => onChange({ ...params, compute_perturbation: v })}
      />

      {isV2 && (
        <Checkbox
          label="Find all branches"
          checked={params.find_all_branches}
          onChange={(v) => onChange({ ...params, find_all_branches: v })}
        />
      )}

      <Checkbox
        label="Fuel budget"
        checked={fuelEnabled}
        onChange={(v) =>
          onChange({
            ...params,
            exhaust_velocity_c: v ? 0.1 : null,
          })
        }
      />

      {fuelEnabled && (
        <ParamInput
          label="Exhaust velocity"
          unit="c"
          value={params.exhaust_velocity_c ?? 0.1}
          min={0.01}
          max={0.5}
          step={0.01}
          onChange={(v) => onChange({ ...params, exhaust_velocity_c: v })}
        />
      )}

      {isV2 && (
        <>
          <div className="border-border my-1 border-t" />

          <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
            Thrust Profile
          </h2>

          <div className="flex flex-col gap-1">
            <label className="text-text-dim text-xs">Acceleration Profile</label>
            <select
              value={params.acceleration_profile}
              onChange={(e) =>
                onChange({ ...params, acceleration_profile: e.target.value })
              }
              className="bg-surface text-text border-border border px-2 py-1 text-xs"
            >
              <option value="step">Step (instantaneous)</option>
              <option value="linear_ramp">Linear Ramp</option>
              <option value="s_curve">S-Curve (smooth jerk)</option>
            </select>
          </div>

          {params.acceleration_profile !== "step" && (
            <ParamInput
              label="Ramp fraction"
              unit=""
              value={params.ramp_fraction}
              min={0.01}
              max={0.5}
              step={0.01}
              onChange={(v) => onChange({ ...params, ramp_fraction: v })}
            />
          )}

          <Checkbox
            label="G-tolerance limit"
            checked={params.max_acceleration_g !== null}
            onChange={(v) =>
              onChange({
                ...params,
                max_acceleration_g: v ? (params.proper_acceleration_g ?? 1.0) : null,
              })
            }
          />

          {params.max_acceleration_g !== null && (
            <ParamInput
              label="Max sustained g"
              unit="g"
              value={params.max_acceleration_g}
              min={0.5}
              max={9}
              step={0.5}
              onChange={(v) => onChange({ ...params, max_acceleration_g: v })}
            />
          )}
        </>
      )}
    </div>
  );
}
