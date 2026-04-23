import { useCallback, useEffect, useRef, useState } from "react";
import { solveTrajectory } from "./api";
import { EnergyDisplay } from "./components/EnergyDisplay";
import { ExportPanel } from "./components/ExportPanel";
import { FuelBudgetPanel } from "./components/FuelBudgetPanel";
import { GRDiagnosticsPanel } from "./components/GRDiagnosticsPanel";
import { MinkowskiDiagram } from "./components/MinkowskiDiagram";
import { ModeToggle } from "./components/ModeToggle";
import { OrbitalView } from "./components/OrbitalView";
import { ParetoFrontPanel } from "./components/ParetoFrontPanel";
import { ParameterPanel } from "./components/ParameterPanel";
import { PerturbationPanel } from "./components/PerturbationPanel";
import { ProperTimeCurve } from "./components/ProperTimeCurve";
import { ResidualMonitor } from "./components/ResidualMonitor";
import { ResultsPanel } from "./components/ResultsPanel";
import { SolutionPicker } from "./components/SolutionPicker";
import { SweepConfigPanel } from "./components/SweepConfigPanel";
import { SweepResultsPanel } from "./components/SweepResultsPanel";
import { TimelineControls } from "./components/TimelineControls";
import { KineticView } from "./components/kinetic/KineticView";
import { useAnimationState } from "./hooks/useAnimationState";
import { useWorldlineInterpolation } from "./hooks/useWorldlineInterpolation";
import type {
  ParetoResult,
  SolveParams,
  SolveResponse,
  Sweep1DResult,
  Sweep2DResult,
  ViewMode,
} from "./types";

const DEFAULT_PARAMS: SolveParams = {
  t0_years: 0.0,
  tf_years: 2.0,
  proper_time_years: 1.5,
  mass_kg: 1000.0,
  trajectory_model: "constant_velocity",
  proper_acceleration_g: null,
  exhaust_velocity_c: null,
  elliptical_orbit: false,
  find_all_branches: false,
  acceleration_profile: "step",
  ramp_fraction: 0.1,
  max_acceleration_g: null,
  earth_model: null,
  gr_corrections: false,
  compute_perturbation: false,
  target: "earth",
};

export default function App() {
  const [params, setParams] = useState<SolveParams>(DEFAULT_PARAMS);
  const [response, setResponse] = useState<SolveResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<ViewMode>("observer");
  const [selectedBranch, setSelectedBranch] = useState(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  // Planning mode state
  const [sweep1DResult, setSweep1DResult] = useState<Sweep1DResult | null>(null);
  const [sweep2DResult, setSweep2DResult] = useState<Sweep2DResult | null>(null);
  const [paretoResult, setParetoResult] = useState<ParetoResult | null>(null);

  const animation = useAnimationState();

  // Derive active solution/worldline from selected branch
  const activeResponse = (() => {
    if (!response) return null;
    if (response.branches && response.branches.length > 1 && selectedBranch < response.branches.length) {
      const branch = response.branches[selectedBranch]!;
      return {
        ...response,
        solution: branch.solution,
        worldline: branch.worldline,
      };
    }
    return response;
  })();

  const interpolated = useWorldlineInterpolation(activeResponse, animation.progress);

  const doSolve = useCallback(async (p: SolveParams) => {
    setLoading(true);
    setError(null);
    try {
      const data = await solveTrajectory(p);
      setResponse(data);
      setSelectedBranch(0);
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

  // Auto-play animation when a new solution arrives
  const prevResponseRef = useRef(response);
  useEffect(() => {
    if (response !== prevResponseRef.current) {
      prevResponseRef.current = response;
      animation.reset();
      if (response?.solution && !response.error) {
        // Small delay so the UI renders the trajectory first
        const t = setTimeout(() => animation.play(), 150);
        return () => clearTimeout(t);
      }
    }
  }, [response, animation.reset, animation.play]);

  // Spacetime Loom: click-to-solve callbacks
  const handleArrivalTimeChange = useCallback(
    (tf_years: number) => {
      if (tf_years > params.t0_years + 0.1) {
        setParams((prev) => ({
          ...prev,
          tf_years: Math.round(tf_years * 100) / 100,
          proper_time_years: Math.min(prev.proper_time_years, tf_years - prev.t0_years - 0.01),
        }));
      }
    },
    [params.t0_years],
  );

  const handleProperTimeChange = useCallback(
    (tau: number) => {
      if (tau > 0.01 && tau < params.tf_years - params.t0_years) {
        setParams((prev) => ({
          ...prev,
          proper_time_years: Math.round(tau * 100) / 100,
        }));
      }
    },
    [params.tf_years, params.t0_years],
  );

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <h1 className="text-amber text-sm font-bold tracking-widest uppercase">
            MARTE
          </h1>
          <p className="text-text-dim text-xs">
            Multi-frame Astrodynamic Relativistic Trajectory Engine
          </p>
        </div>
        <ModeToggle mode={mode} onChange={setMode} />
      </header>

      {/* Main content */}
      <div className="min-h-0 flex-1">
        {mode === "observer" ? (
          /* Observer mode: existing grid layout */
          <div className="grid h-full grid-cols-[280px_1fr] grid-rows-[1fr_1fr]">
            {/* Left sidebar */}
            <aside className="row-span-2 flex flex-col gap-0 overflow-y-auto border-r border-border">
              <ParameterPanel params={params} onChange={setParams} />
              {response?.branches && response.branches.length > 1 && (
                <SolutionPicker
                  branches={response.branches}
                  selectedIndex={selectedBranch}
                  onSelect={setSelectedBranch}
                />
              )}
              <div className="border-t border-border">
                <ResultsPanel response={activeResponse} loading={loading} />
              </div>
              <div className="border-t border-border">
                <EnergyDisplay response={activeResponse} />
              </div>
              {response?.fuel_budget && (
                <div className="border-t border-border">
                  <FuelBudgetPanel fuelBudget={response.fuel_budget} />
                </div>
              )}
              <div className="border-t border-border">
                <ResidualMonitor convergence={response?.convergence ?? null} />
              </div>
              {response?.gr_diagnostics && (
                <div className="border-t border-border">
                  <GRDiagnosticsPanel diagnostics={response.gr_diagnostics} />
                </div>
              )}
              {response?.perturbation && (
                <div className="border-t border-border">
                  <PerturbationPanel perturbation={response.perturbation} />
                </div>
              )}
              <div className="border-t border-border">
                <ExportPanel params={params} response={response} />
              </div>
            </aside>

            {/* 3D orbital view */}
            <main className="relative min-h-0 border-b border-border">
              {loading && (
                <div className="text-amber absolute top-2 right-2 z-10 text-xs">
                  COMPUTING...
                </div>
              )}
              {error && !activeResponse?.solution && (
                <div className="flex h-full items-center justify-center">
                  <p className="text-red text-sm">{error}</p>
                </div>
              )}
              {activeResponse?.solution && activeResponse.worldline && activeResponse.earth && (
                <OrbitalView
                  worldline={activeResponse.worldline}
                  earth={activeResponse.earth}
                  interpolated={interpolated}
                  targetTrajectory={activeResponse.target_trajectory}
                />
              )}
            </main>

            {/* Bottom: two plots */}
            <div className="grid min-h-0 grid-cols-2">
              <div className="min-h-0 border-r border-border">
                {activeResponse?.solution && activeResponse.worldline && activeResponse.earth && (
                  <MinkowskiDiagram
                    worldline={activeResponse.worldline}
                    earth={activeResponse.earth}
                    interpolated={interpolated}
                    branches={response?.branches}
                    selectedBranch={selectedBranch}
                    onArrivalTimeChange={handleArrivalTimeChange}
                  />
                )}
              </div>
              <div className="min-h-0">
                {activeResponse?.solution && activeResponse.worldline && (
                  <ProperTimeCurve
                    worldline={activeResponse.worldline}
                    interpolated={interpolated}
                    onProperTimeChange={handleProperTimeChange}
                  />
                )}
              </div>
            </div>
          </div>
        ) : mode === "kinetic" ? (
          /* Kinetic mode: full-screen cockpit view */
          <div className="relative h-full">
            {!activeResponse?.solution || !activeResponse.worldline || !activeResponse.earth ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-text-dim text-sm">
                  {loading ? "COMPUTING..." : error ?? "Waiting for solution..."}
                </p>
              </div>
            ) : (
              <KineticView
                response={activeResponse}
                interpolated={interpolated}
                animation={animation}
              />
            )}
          </div>
        ) : (
          /* Planning mode: mission planning interface */
          <div className="grid h-full grid-cols-[300px_1fr]">
            {/* Left panel: config */}
            <aside className="flex flex-col gap-0 overflow-y-auto border-r border-border">
              <ParameterPanel params={params} onChange={setParams} />
              <div className="border-t border-border">
                <SweepConfigPanel
                  params={params}
                  onSweep1D={(r) => { setSweep1DResult(r); setSweep2DResult(null); }}
                  onSweep2D={(r) => { setSweep2DResult(r); setSweep1DResult(null); }}
                />
              </div>
              <div className="border-t border-border">
                <ParetoFrontPanel
                  params={params}
                  onResult={setParetoResult}
                  result={paretoResult}
                />
              </div>
              <div className="border-t border-border">
                <ExportPanel params={params} response={response} />
              </div>
            </aside>

            {/* Right area: results */}
            <div className="grid h-full grid-rows-2">
              {/* Top: orbital view or sweep results */}
              <div className="relative min-h-0 border-b border-border">
                {activeResponse?.solution && activeResponse.worldline && activeResponse.earth ? (
                  <OrbitalView
                    worldline={activeResponse.worldline}
                    earth={activeResponse.earth}
                    interpolated={interpolated}
                    targetTrajectory={activeResponse.target_trajectory}
                  />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-text-dim text-sm">
                      {loading ? "COMPUTING..." : error ?? "Configure parameters to begin"}
                    </p>
                  </div>
                )}
              </div>

              {/* Bottom: sweep/pareto results */}
              <div className="min-h-0 overflow-auto">
                <SweepResultsPanel
                  sweep1D={sweep1DResult}
                  sweep2D={sweep2DResult}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline controls (all modes) */}
      <TimelineControls animation={animation} interpolated={interpolated} />
    </div>
  );
}
