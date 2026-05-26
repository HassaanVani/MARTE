import { useCallback, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import type { SolutionData, WorldlineData } from "../types";

interface Props {
  worldline: WorldlineData;
  solution: SolutionData;
}

/* ─── Shared Plotly layout tokens ─── */

const FONT: Partial<Plotly.Font> = {
  family: "JetBrains Mono, monospace",
  size: 11,
  color: "#e4e4e7",
};

const AXIS_STYLE: Partial<Plotly.LayoutAxis> = {
  gridcolor: "#1e1e21",
  zerolinecolor: "#3f3f46",
  color: "#a1a1aa",
  linecolor: "#27272a",
};

const PAPER_BG = "#09090b";
const PLOT_BG = "#09090b";
const AMBER = "#f59e0b";
const CYAN = "#06b6d4";
const RED = "#ef4444";
const DIM = "#71717a";
const TRAPEZOID_FILL = "rgba(6,182,212,0.12)";
const TRAPEZOID_STROKE = "rgba(6,182,212,0.5)";

/* ─── Pure math helpers ─── */

function gammaFromBeta(beta: number): number {
  const ombs = (1 - beta) * (1 + beta);
  return ombs > 0 ? 1 / Math.sqrt(ombs) : 1e8;
}

/** Resample arrays to `n` evenly-spaced points via linear interpolation. */
function resample(tauFull: number[], gammaFull: number[], n: number): { tau: number[]; gamma: number[] } {
  if (n >= tauFull.length) return { tau: tauFull, gamma: gammaFull };
  const tauMin = tauFull[0]!;
  const tauMax = tauFull[tauFull.length - 1]!;
  const step = (tauMax - tauMin) / (n - 1);
  const tau: number[] = [];
  const gamma: number[] = [];
  let j = 0;
  for (let i = 0; i < n; i++) {
    const t = tauMin + i * step;
    tau.push(t);
    // advance j
    while (j < tauFull.length - 2 && tauFull[j + 1]! < t) j++;
    const t0 = tauFull[j]!;
    const t1 = tauFull[j + 1]!;
    const frac = t1 > t0 ? (t - t0) / (t1 - t0) : 0;
    gamma.push(gammaFull[j]! + frac * (gammaFull[j + 1]! - gammaFull[j]!));
  }
  return { tau, gamma };
}

/** Trapezoidal integration returning cumulative sums. */
function trapezoidalCumulative(tau: number[], gamma: number[]): number[] {
  const cum: number[] = [0];
  for (let i = 1; i < tau.length; i++) {
    const dt = tau[i]! - tau[i - 1]!;
    const area = 0.5 * (gamma[i - 1]! + gamma[i]!) * dt;
    cum.push(cum[i - 1]! + area);
  }
  return cum;
}

/* ─── Component ─── */

export function CalculusView({ worldline, solution }: Props) {
  const betaProfile = worldline.beta_profile;
  const maxN = betaProfile ? betaProfile.length : worldline.proper_times_s.length;

  const [nTrapezoids, setNTrapezoids] = useState(Math.min(16, maxN));
  const [showError, setShowError] = useState(true);

  // Full-resolution γ(τ) curve
  const fullData = useMemo(() => {
    const tauS = worldline.proper_times_s;
    const gamma: number[] = [];
    if (betaProfile && betaProfile.length === tauS.length) {
      for (let i = 0; i < tauS.length; i++) {
        gamma.push(gammaFromBeta(betaProfile[i]!));
      }
    } else {
      // Fallback: derive β from Δx/Δt
      const ct = worldline.coord_times_s;
      gamma.push(1.0);
      for (let i = 1; i < ct.length; i++) {
        const dt = ct[i]! - ct[i - 1]!;
        const dtau = tauS[i]! - tauS[i - 1]!;
        const g = dtau > 0 ? dt / dtau : 1.0;
        gamma.push(Math.max(1.0, g));
      }
    }
    return { tau: tauS, gamma };
  }, [worldline, betaProfile]);

  // Resampled data at current N
  const sampledData = useMemo(() => {
    return resample(fullData.tau, fullData.gamma, Math.max(2, nTrapezoids));
  }, [fullData, nTrapezoids]);

  // Cumulative integral at current N
  const cumulativeApprox = useMemo(() => {
    return trapezoidalCumulative(sampledData.tau, sampledData.gamma);
  }, [sampledData]);

  // "Exact" cumulative (full-resolution trapezoidal = engine's answer)
  const cumulativeExact = useMemo(() => {
    return trapezoidalCumulative(fullData.tau, fullData.gamma);
  }, [fullData]);

  // Exact total coordinate time from the engine
  const exactTotal = worldline.coord_times_s[worldline.coord_times_s.length - 1]! - worldline.coord_times_s[0]!;
  const approxTotal = cumulativeApprox[cumulativeApprox.length - 1]!;
  const absError = Math.abs(approxTotal - exactTotal);
  const relError = exactTotal > 0 ? absError / exactTotal : 0;

  // Error convergence data (sweep N = 2,3,4,6,8,12,16,24,32,48,64,...,maxN)
  const convergenceData = useMemo(() => {
    const ns: number[] = [];
    const errors: number[] = [];
    // Generate a geometric-ish sequence
    const candidates = [2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512];
    for (const n of candidates) {
      if (n > maxN) break;
      ns.push(n);
      const s = resample(fullData.tau, fullData.gamma, n);
      const cum = trapezoidalCumulative(s.tau, s.gamma);
      const total = cum[cum.length - 1]!;
      errors.push(Math.abs(total - exactTotal));
    }
    // Always include maxN
    if (ns[ns.length - 1] !== maxN && maxN > 2) {
      ns.push(maxN);
      const s = resample(fullData.tau, fullData.gamma, maxN);
      const cum = trapezoidalCumulative(s.tau, s.gamma);
      errors.push(Math.abs(cum[cum.length - 1]! - exactTotal));
    }
    return { ns, errors };
  }, [fullData, maxN, exactTotal]);

  // ──────────────────────────────────
  // Panel 1: γ(τ) with trapezoids
  // ──────────────────────────────────

  const trapezoidTraces = useMemo((): Plotly.Data[] => {
    const traces: Plotly.Data[] = [];

    // Smooth full-resolution curve
    traces.push({
      x: fullData.tau,
      y: fullData.gamma,
      mode: "lines",
      line: { color: CYAN, width: 2 },
      name: "γ(τ) = cosh(φ)",
      hovertemplate: "τ = %{x:.2f} s<br>γ = %{y:.6f}<extra></extra>",
    });

    // Trapezoid tops (piecewise linear approximation)
    traces.push({
      x: sampledData.tau,
      y: sampledData.gamma,
      mode: "lines+markers",
      line: { color: AMBER, width: 1.5, dash: "dot" },
      marker: { size: 5, color: AMBER },
      name: `Trapezoidal (N=${nTrapezoids})`,
      hovertemplate: "τ = %{x:.2f} s<br>γ ≈ %{y:.6f}<extra></extra>",
    });

    // Filled trapezoids as individual filled shapes
    for (let i = 0; i < sampledData.tau.length - 1; i++) {
      const x0 = sampledData.tau[i]!;
      const x1 = sampledData.tau[i + 1]!;
      const y0 = sampledData.gamma[i]!;
      const y1 = sampledData.gamma[i + 1]!;
      traces.push({
        x: [x0, x1, x1, x0, x0],
        y: [0, 0, y1, y0, 0],
        fill: "toself",
        fillcolor: TRAPEZOID_FILL,
        line: { color: TRAPEZOID_STROKE, width: 0.5 },
        mode: "lines",
        showlegend: false,
        hoverinfo: "skip",
      } as Plotly.Data);
    }

    return traces;
  }, [fullData, sampledData, nTrapezoids]);

  const trapezoidLayout = useMemo((): Partial<Plotly.Layout> => ({
    paper_bgcolor: PAPER_BG,
    plot_bgcolor: PLOT_BG,
    font: FONT,
    margin: { l: 60, r: 20, t: 40, b: 50 },
    xaxis: { ...AXIS_STYLE, title: { text: "Proper time τ (s)" } },
    yaxis: { ...AXIS_STYLE, title: { text: "Lorentz factor γ" }, rangemode: "tozero" },
    showlegend: true,
    legend: { x: 0.02, y: 0.98, font: { size: 9, color: DIM }, bgcolor: "transparent" },
    title: {
      text: "∫ γ(τ) dτ  —  TRAPEZOIDAL APPROXIMATION",
      font: { size: 11, color: AMBER },
    },
    annotations: [
      {
        x: 0.98,
        y: 0.02,
        xref: "paper",
        yref: "paper",
        text: `∫₀ᵀ γ(τ)dτ ≈ Σ ½(γᵢ + γᵢ₊₁)Δτ`,
        showarrow: false,
        font: { size: 10, color: DIM },
        xanchor: "right",
      },
    ],
  }), []);

  // ──────────────────────────────────
  // Panel 2: Cumulative integral
  // ──────────────────────────────────

  const cumulativeTraces = useMemo((): Plotly.Data[] => {
    const traces: Plotly.Data[] = [];

    // Exact (full-resolution)
    traces.push({
      x: fullData.tau,
      y: cumulativeExact,
      mode: "lines",
      line: { color: CYAN, width: 2 },
      name: "Exact (engine)",
      hovertemplate: "τ = %{x:.2f} s<br>t = %{y:.4f} s<extra></extra>",
    });

    // Approximate at current N
    traces.push({
      x: sampledData.tau,
      y: cumulativeApprox,
      mode: "lines+markers",
      line: { color: AMBER, width: 1.5 },
      marker: { size: 4, color: AMBER },
      name: `N = ${nTrapezoids}`,
      hovertemplate: "τ = %{x:.2f} s<br>t ≈ %{y:.4f} s<extra></extra>",
    });

    // Error shading between curves (only if toggled)
    if (showError && sampledData.tau.length > 1) {
      // Interpolate exact values at sample points for error fill
      const exactAtSample = resample(fullData.tau, cumulativeExact, sampledData.tau.length);
      traces.push({
        x: [...sampledData.tau, ...([...sampledData.tau].reverse())],
        y: [...cumulativeApprox, ...([...exactAtSample.gamma].reverse())],
        fill: "toself",
        fillcolor: "rgba(239,68,68,0.1)",
        line: { color: "transparent" },
        mode: "lines",
        showlegend: false,
        hoverinfo: "skip",
        name: "Error region",
      } as Plotly.Data);
    }

    return traces;
  }, [fullData, sampledData, cumulativeApprox, cumulativeExact, nTrapezoids, showError]);

  const cumulativeLayout = useMemo((): Partial<Plotly.Layout> => ({
    paper_bgcolor: PAPER_BG,
    plot_bgcolor: PLOT_BG,
    font: FONT,
    margin: { l: 60, r: 20, t: 40, b: 50 },
    xaxis: { ...AXIS_STYLE, title: { text: "Proper time τ (s)" } },
    yaxis: { ...AXIS_STYLE, title: { text: "Coordinate time t (s)" } },
    showlegend: true,
    legend: { x: 0.02, y: 0.98, font: { size: 9, color: DIM }, bgcolor: "transparent" },
    title: {
      text: "CUMULATIVE INTEGRAL  —  t(τ) = ∫₀ᵗ γ dτ′",
      font: { size: 11, color: AMBER },
    },
  }), []);

  // ──────────────────────────────────
  // Panel 3: Error convergence
  // ──────────────────────────────────

  const convergenceTraces = useMemo((): Plotly.Data[] => {
    const traces: Plotly.Data[] = [];

    // Filter out zero errors for log scale
    const validNs: number[] = [];
    const validErrors: number[] = [];
    for (let i = 0; i < convergenceData.ns.length; i++) {
      if (convergenceData.errors[i]! > 0) {
        validNs.push(convergenceData.ns[i]!);
        validErrors.push(convergenceData.errors[i]!);
      }
    }

    // Actual error points
    traces.push({
      x: validNs,
      y: validErrors,
      mode: "lines+markers",
      line: { color: RED, width: 2 },
      marker: { size: 6, color: RED },
      name: "|Error|",
      hovertemplate: "N = %{x}<br>|ε| = %{y:.4e} s<extra></extra>",
    });

    // O(N⁻²) reference line
    if (validNs.length >= 2) {
      const refN0 = validNs[0]!;
      const refE0 = validErrors[0]!;
      const refLine = validNs.map((n) => refE0 * (refN0 / n) ** 2);
      traces.push({
        x: validNs,
        y: refLine,
        mode: "lines",
        line: { color: DIM, width: 1, dash: "dash" },
        name: "O(N⁻²) reference",
        hoverinfo: "skip",
      });
    }

    // Current N marker
    const currentIdx = validNs.indexOf(nTrapezoids);
    if (currentIdx >= 0) {
      traces.push({
        x: [validNs[currentIdx]!],
        y: [validErrors[currentIdx]!],
        mode: "markers",
        marker: { size: 12, color: AMBER, symbol: "diamond" },
        name: "Current N",
        showlegend: false,
      });
    }

    return traces;
  }, [convergenceData, nTrapezoids]);

  const convergenceLayout = useMemo((): Partial<Plotly.Layout> => ({
    paper_bgcolor: PAPER_BG,
    plot_bgcolor: PLOT_BG,
    font: FONT,
    margin: { l: 70, r: 20, t: 40, b: 50 },
    xaxis: { ...AXIS_STYLE, title: { text: "Number of trapezoids N" }, type: "log" },
    yaxis: { ...AXIS_STYLE, title: { text: "|Error| (s)" }, type: "log" },
    showlegend: true,
    legend: { x: 0.6, y: 0.98, font: { size: 9, color: DIM }, bgcolor: "transparent" },
    title: {
      text: "ERROR CONVERGENCE  —  O(N⁻²)",
      font: { size: 11, color: AMBER },
    },
  }), []);

  const handleSlider = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNTrapezoids(parseInt(e.target.value, 10));
  }, []);

  // Format helpers
  const fmtSci = (v: number) => v.toExponential(3);
  const fmtFixed = (v: number, d = 4) => v.toFixed(d);

  const peakGamma = solution.peak_gamma ?? solution.gamma;

  return (
    <div className="flex h-full flex-col">
      {/* ── Control bar ── */}
      <div className="flex items-center gap-6 border-b border-border px-4 py-2">
        <div className="flex items-center gap-2">
          <label className="text-text-dim text-xs font-bold uppercase tracking-widest">
            Trapezoids
          </label>
          <input
            id="calculus-n-slider"
            type="range"
            min={2}
            max={maxN}
            step={1}
            value={nTrapezoids}
            onChange={handleSlider}
            className="calculus-slider w-40"
          />
          <span className="text-amber w-12 text-right text-xs font-bold tabular-nums">
            {nTrapezoids}
          </span>
        </div>

        <button
          id="calculus-error-toggle"
          onClick={() => setShowError((s) => !s)}
          className={`px-2 py-1 text-xs font-bold uppercase tracking-widest transition-colors ${
            showError
              ? "bg-red/20 text-red border border-red/30"
              : "text-text-dim border border-border hover:border-red/30"
          }`}
        >
          Error Fill
        </button>

        <div className="ml-auto flex gap-6 text-xs">
          <div>
            <span className="text-text-dim mr-1">γ_peak:</span>
            <span className="text-cyan font-bold">{fmtFixed(peakGamma, 6)}</span>
          </div>
          <div>
            <span className="text-text-dim mr-1">∫γ dτ (exact):</span>
            <span className="text-cyan font-bold">{fmtFixed(exactTotal, 2)} s</span>
          </div>
          <div>
            <span className="text-text-dim mr-1">∫γ dτ (N={nTrapezoids}):</span>
            <span className="text-amber font-bold">{fmtFixed(approxTotal, 2)} s</span>
          </div>
          <div>
            <span className="text-text-dim mr-1">|ε|:</span>
            <span className="text-red font-bold">{fmtSci(absError)} s</span>
          </div>
          <div>
            <span className="text-text-dim mr-1">ε_rel:</span>
            <span className="text-red font-bold">{fmtSci(relError)}</span>
          </div>
        </div>
      </div>

      {/* ── Chart grid ── */}
      <div className="grid min-h-0 flex-1 grid-cols-2 grid-rows-2">
        {/* Left: spans both rows — trapezoid visualization */}
        <div className="row-span-2 min-h-0 border-r border-border">
          <Plot
            data={trapezoidTraces}
            layout={trapezoidLayout}
            config={{ responsive: true, displayModeBar: false }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        </div>

        {/* Top-right: cumulative integral */}
        <div className="min-h-0 border-b border-border">
          <Plot
            data={cumulativeTraces}
            layout={cumulativeLayout}
            config={{ responsive: true, displayModeBar: false }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        </div>

        {/* Bottom-right: error convergence */}
        <div className="min-h-0">
          <Plot
            data={convergenceTraces}
            layout={convergenceLayout}
            config={{ responsive: true, displayModeBar: false }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      </div>
    </div>
  );
}
