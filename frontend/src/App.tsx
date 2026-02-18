import { useCallback, useEffect, useRef, useState } from "react";
import { solveTrajectory } from "./api";
import { EnergyDisplay } from "./components/EnergyDisplay";
import { MinkowskiDiagram } from "./components/MinkowskiDiagram";
import { OrbitalView } from "./components/OrbitalView";
import { ParameterPanel } from "./components/ParameterPanel";
import { ProperTimeCurve } from "./components/ProperTimeCurve";
import { ResultsPanel } from "./components/ResultsPanel";
import type { SolveParams, SolveResponse } from "./types";

const DEFAULT_PARAMS: SolveParams = {
  t0_years: 0.0,
  tf_years: 2.0,
  proper_time_years: 1.5,
  mass_kg: 1000.0,
  trajectory_model: "constant_velocity",
  proper_acceleration_g: null,
};

export default function App() {
  const [params, setParams] = useState<SolveParams>(DEFAULT_PARAMS);
  const [response, setResponse] = useState<SolveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  const doSolve = useCallback(async (p: SolveParams) => {
    setLoading(true);
    setError(null);
    try {
      const data = await solveTrajectory(p);
      setResponse(data);
      if (data.error) {
        setError(data.error);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSolve(params), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [params, doSolve]);

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-border px-4 py-3">
        <h1 className="text-amber text-sm font-bold tracking-widest uppercase">
          MARTE
        </h1>
        <p className="text-text-dim text-xs">
          Multi-frame Astrodynamic Relativistic Trajectory Engine
        </p>
      </header>

      {/* Main grid */}
      <div className="grid min-h-0 flex-1 grid-cols-[280px_1fr] grid-rows-[1fr_1fr]">
        {/* Left sidebar — spans both rows */}
        <aside className="row-span-2 flex flex-col gap-0 overflow-y-auto border-r border-border">
          <ParameterPanel params={params} onChange={setParams} />
          <div className="border-t border-border">
            <ResultsPanel response={response} loading={loading} />
          </div>
          <div className="border-t border-border">
            <EnergyDisplay response={response} />
          </div>
        </aside>

        {/* 3D orbital view — top right */}
        <main className="relative min-h-0 border-b border-border">
          {loading && (
            <div className="text-amber absolute top-2 right-2 z-10 text-xs">
              COMPUTING...
            </div>
          )}
          {error && !response?.solution && (
            <div className="flex h-full items-center justify-center">
              <p className="text-red text-sm">{error}</p>
            </div>
          )}
          {response?.solution && response.worldline && response.earth && (
            <OrbitalView
              worldline={response.worldline}
              earth={response.earth}
            />
          )}
        </main>

        {/* Bottom right — two plots side by side */}
        <div className="grid min-h-0 grid-cols-2">
          <div className="min-h-0 border-r border-border">
            {response?.solution && response.worldline && response.earth && (
              <MinkowskiDiagram
                worldline={response.worldline}
                earth={response.earth}
              />
            )}
          </div>
          <div className="min-h-0">
            {response?.solution && response.worldline && (
              <ProperTimeCurve worldline={response.worldline} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
