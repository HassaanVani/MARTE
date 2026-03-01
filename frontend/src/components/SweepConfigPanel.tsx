import { useState } from "react";
import { sweep1D, sweep2D } from "../api";
import type { SolveParams, Sweep1DResult, Sweep2DResult } from "../types";

const SWEEPABLE_PARAMS = [
  { value: "tf_years", label: "Arrival time (yr)" },
  { value: "proper_time_years", label: "Proper time (yr)" },
  { value: "mass_kg", label: "Ship mass (kg)" },
  { value: "proper_acceleration_g", label: "Acceleration (g)" },
];

interface Props {
  params: SolveParams;
  onSweep1D: (result: Sweep1DResult) => void;
  onSweep2D: (result: Sweep2DResult) => void;
}

export function SweepConfigPanel({ params, onSweep1D, onSweep2D }: Props) {
  const [mode, setMode] = useState<"1d" | "2d">("1d");
  const [loading, setLoading] = useState(false);

  // 1D config
  const [param1, setParam1] = useState("tf_years");
  const [min1, setMin1] = useState(1);
  const [max1, setMax1] = useState(5);
  const [steps1, setSteps1] = useState(20);

  // 2D config
  const [xParam, setXParam] = useState("tf_years");
  const [xMin, setXMin] = useState(1);
  const [xMax, setXMax] = useState(5);
  const [yParam, setYParam] = useState("proper_time_years");
  const [yMin, setYMin] = useState(0.5);
  const [yMax, setYMax] = useState(4);
  const [xSteps, setXSteps] = useState(15);
  const [ySteps, setYSteps] = useState(15);

  const handleRun = async () => {
    setLoading(true);
    try {
      if (mode === "1d") {
        const result = await sweep1D(params, {
          param_name: param1,
          min_value: min1,
          max_value: max1,
          steps: steps1,
        });
        onSweep1D(result);
      } else {
        const result = await sweep2D(params, {
          x_param: xParam,
          x_min: xMin,
          x_max: xMax,
          y_param: yParam,
          y_min: yMin,
          y_max: yMax,
          x_steps: xSteps,
          y_steps: ySteps,
        });
        onSweep2D(result);
      }
    } catch {
      // sweep failed
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Parameter Sweep
      </h2>

      {/* Mode toggle */}
      <div className="flex gap-1">
        <button
          onClick={() => setMode("1d")}
          className={`flex-1 px-2 py-1 text-xs font-bold ${mode === "1d" ? "bg-amber text-bg" : "border border-border text-text-dim"}`}
        >
          1D Curve
        </button>
        <button
          onClick={() => setMode("2d")}
          className={`flex-1 px-2 py-1 text-xs font-bold ${mode === "2d" ? "bg-amber text-bg" : "border border-border text-text-dim"}`}
        >
          2D Heatmap
        </button>
      </div>

      {mode === "1d" ? (
        <div className="flex flex-col gap-1">
          <label className="text-text-dim text-xs">Parameter</label>
          <select value={param1} onChange={(e) => setParam1(e.target.value)} className="bg-surface text-text border-border border px-2 py-1 text-xs">
            {SWEEPABLE_PARAMS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <div className="grid grid-cols-3 gap-1">
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Min</span>
              <input type="number" value={min1} step={0.1} onChange={(e) => setMin1(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Max</span>
              <input type="number" value={max1} step={0.1} onChange={(e) => setMax1(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Steps</span>
              <input type="number" value={steps1} min={2} max={50} onChange={(e) => setSteps1(+e.target.value)} className="w-full" />
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-1">
          <label className="text-text-dim text-xs">X Parameter</label>
          <select value={xParam} onChange={(e) => setXParam(e.target.value)} className="bg-surface text-text border-border border px-2 py-1 text-xs">
            {SWEEPABLE_PARAMS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <div className="grid grid-cols-3 gap-1">
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Min</span>
              <input type="number" value={xMin} step={0.1} onChange={(e) => setXMin(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Max</span>
              <input type="number" value={xMax} step={0.1} onChange={(e) => setXMax(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Steps</span>
              <input type="number" value={xSteps} min={2} max={30} onChange={(e) => setXSteps(+e.target.value)} className="w-full" />
            </div>
          </div>
          <label className="text-text-dim text-xs mt-1">Y Parameter</label>
          <select value={yParam} onChange={(e) => setYParam(e.target.value)} className="bg-surface text-text border-border border px-2 py-1 text-xs">
            {SWEEPABLE_PARAMS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <div className="grid grid-cols-3 gap-1">
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Min</span>
              <input type="number" value={yMin} step={0.1} onChange={(e) => setYMin(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Max</span>
              <input type="number" value={yMax} step={0.1} onChange={(e) => setYMax(+e.target.value)} className="w-full" />
            </div>
            <div className="flex flex-col">
              <span className="text-text-dim text-[10px]">Steps</span>
              <input type="number" value={ySteps} min={2} max={30} onChange={(e) => setYSteps(+e.target.value)} className="w-full" />
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={loading}
        className="bg-amber text-bg mt-1 px-2 py-1.5 text-xs font-bold uppercase tracking-widest disabled:opacity-50"
      >
        {loading ? "Running..." : "Run Sweep"}
      </button>
    </div>
  );
}
