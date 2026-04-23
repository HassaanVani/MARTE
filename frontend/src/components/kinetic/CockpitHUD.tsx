import { useEffect, useRef, useState } from "react";
import type { InterpolatedState } from "../../types";

interface Props {
  interpolated: InterpolatedState | null;
}

const SPEED_OF_LIGHT_KMS = 299_792.458;
const G = 9.806_65;

// --- Formatting helpers ---

function formatSpeed(kms: number): string {
  if (kms < 1000) return kms.toFixed(1);
  if (kms < 1_000_000) return (kms / 1000).toFixed(1) + "k";
  return kms.toLocaleString("en", { maximumFractionDigits: 0 });
}

function formatEnergy(joules: number): { value: string; unit: string } {
  if (joules < 1e12) return { value: joules.toExponential(2), unit: "J" };
  if (joules < 1e15) return { value: (joules / 1e12).toFixed(1), unit: "TJ" };
  if (joules < 1e18) return { value: (joules / 1e15).toFixed(1), unit: "PJ" };
  if (joules < 1e21) return { value: (joules / 1e18).toFixed(1), unit: "EJ" };
  return { value: (joules / 1e21).toFixed(1), unit: "ZJ" };
}

/** Return a human-scale reference for the energy */
function energyScale(joules: number): string | null {
  if (joules < 1e16) return null;
  const globalAnnual = 5.8e20; // ~580 EJ global annual energy consumption
  const tsarBomba = 2.1e17;
  if (joules < 1e18) return `~${(joules / tsarBomba).toFixed(0)} Tsar Bomba`;
  const pct = (joules / globalAnnual) * 100;
  if (pct < 1) return `~${pct.toFixed(1)}% global annual`;
  if (pct < 100) return `~${pct.toFixed(0)}% global annual`;
  return `~${(pct / 100).toFixed(0)}× global annual`;
}

function energyClass(joules: number): string {
  if (joules < 1e17) return "energy-nominal";
  if (joules < 1e20) return "energy-elevated";
  return "energy-extreme";
}

/** What spectral band does the Doppler-shifted visible light fall into? */
function dopplerBand(doppler: number): string {
  // Doppler > 1 = blueshift, < 1 = redshift
  // Visible ~380-700nm, shifted by 1/D
  if (doppler > 4.0) return "X-RAY";
  if (doppler > 2.5) return "UV";
  if (doppler > 1.5) return "BLUE";
  if (doppler > 0.7) return "VIS";
  if (doppler > 0.4) return "IR";
  if (doppler > 0.15) return "FAR-IR";
  return "RADIO";
}

function dopplerBandColor(band: string): string {
  switch (band) {
    case "X-RAY": return "#c084fc";   // violet
    case "UV":    return "#818cf8";    // indigo
    case "BLUE":  return "#60a5fa";    // blue
    case "VIS":   return "#e4e4e7";    // white
    case "IR":    return "#f87171";    // red
    case "FAR-IR": return "#991b1b";   // dark red
    case "RADIO": return "#451a03";    // near-black brown
    default:      return "#e4e4e7";
  }
}

export function CockpitHUD({ interpolated }: Props) {
  const [showTurnaroundFlash, setShowTurnaroundFlash] = useState(false);
  const prevPhaseRef = useRef<string | null>(null);

  // Detect phase transition to TURNAROUND
  useEffect(() => {
    if (!interpolated) return;
    const prev = prevPhaseRef.current;
    prevPhaseRef.current = interpolated.phase;
    if (interpolated.phase === "TURNAROUND" && prev !== "TURNAROUND" && prev !== null) {
      setShowTurnaroundFlash(true);
      const timer = setTimeout(() => setShowTurnaroundFlash(false), 1500);
      return () => clearTimeout(timer);
    }
  }, [interpolated?.phase]);

  if (!interpolated) return null;

  const {
    coordTime, properTime, beta, gamma, phase,
    distanceToEarth, lightDelaySeconds,
    dopplerForward, dopplerAft,
    properAcceleration, energyJoules, rapidity,
    turnaroundProximity,
  } = interpolated;

  const speedKms = beta * SPEED_OF_LIGHT_KMS;
  const timeDivergence = coordTime - properTime;
  const betaPct = (beta * 100).toFixed(1);
  const accelG = properAcceleration / G;
  const isThrusting = phase === "ACCELERATING" || phase === "DECELERATING";
  const energy = formatEnergy(energyJoules);
  const scale = energyScale(energyJoules);
  const fwdBand = dopplerBand(dopplerForward);
  const aftBand = dopplerBand(dopplerAft);
  const nearTurnaround = turnaroundProximity > 0;

  return (
    <div className="hud-overlay pointer-events-none absolute inset-0 z-10">
      {/* Cockpit vignette */}
      <div className="cockpit-vignette absolute inset-0" />

      {/* Cockpit frame edges */}
      <div className="absolute inset-0">
        <div className="absolute top-0 right-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-amber/20 to-transparent" />
        <div className="absolute right-0 bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-amber/20 to-transparent" />
        <div className="absolute top-3 left-3 h-6 w-6 border-t border-l border-amber/30" />
        <div className="absolute top-3 right-3 h-6 w-6 border-t border-r border-amber/30" />
        <div className="absolute bottom-3 left-3 h-6 w-6 border-b border-l border-amber/30" />
        <div className="absolute right-3 bottom-3 h-6 w-6 border-b border-r border-amber/30" />
      </div>

      {/* === TOP ROW === */}

      {/* Top-left: Ship Clock */}
      <div className="hud-panel absolute top-6 left-6">
        <div className="hud-label">SHIP CLOCK</div>
        <div className="text-cyan hud-value text-3xl">
          {properTime.toFixed(4)}
          <span className="text-cyan/50 ml-1 text-sm">YR</span>
        </div>
      </div>

      {/* Top-right: Home Clock */}
      <div className="hud-panel absolute top-6 right-6 text-right">
        <div className="hud-label">EARTH CLOCK</div>
        <div className="text-text hud-value text-3xl">
          {coordTime.toFixed(4)}
          <span className="text-text-dim ml-1 text-sm">YR</span>
        </div>
        {timeDivergence > 0.001 && (
          <div className={`mt-0.5 text-xs tabular-nums ${
            timeDivergence > coordTime * 0.1 ? "text-amber hud-warning" : "text-amber"
          }`}>
            Δ +{timeDivergence.toFixed(4)} yr
          </div>
        )}
      </div>

      {/* Center top: Phase */}
      <div className="absolute top-6 left-1/2 -translate-x-1/2">
        <div className="hud-panel-center">
          <div className="hud-label text-center">PHASE</div>
          <div className="text-amber text-center text-lg font-bold tracking-[0.4em]">
            {phase}
          </div>
        </div>
      </div>

      {/* === CENTER === */}

      {/* Center: Crosshair + velocity ring */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <svg width="120" height="120" viewBox="0 0 120 120" className="opacity-40">
          <circle cx="60" cy="60" r="50" stroke="#f59e0b" strokeWidth="0.5" fill="none" />
          <line x1="60" y1="6" x2="60" y2="14" stroke="#f59e0b" strokeWidth="1" />
          <line x1="60" y1="106" x2="60" y2="114" stroke="#f59e0b" strokeWidth="1" />
          <line x1="6" y1="60" x2="14" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <line x1="106" y1="60" x2="114" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <line x1="60" y1="45" x2="60" y2="53" stroke="#f59e0b" strokeWidth="1" />
          <line x1="60" y1="67" x2="60" y2="75" stroke="#f59e0b" strokeWidth="1" />
          <line x1="45" y1="60" x2="53" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <line x1="67" y1="60" x2="75" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <circle cx="60" cy="60" r="1.5" fill="#f59e0b" />
          {/* Speed arc — fills proportional to β */}
          <circle
            cx="60"
            cy="60"
            r="50"
            stroke="#f59e0b"
            strokeWidth="2"
            fill="none"
            strokeDasharray={`${beta * 314} 314`}
            strokeDashoffset="78.5"
            strokeLinecap="round"
          />
        </svg>
      </div>

      {/* === Turnaround flash overlay === */}
      {showTurnaroundFlash && (
        <div className="turnaround-flash absolute inset-0 flex items-center justify-center">
          <div className="text-amber text-5xl font-bold tracking-[0.5em] drop-shadow-[0_0_20px_rgba(245,158,11,0.5)]">
            TURNAROUND
          </div>
        </div>
      )}

      {/* === LEFT COLUMN (bottom area) === */}

      {/* Bottom-left: Velocity panel */}
      <div className="hud-panel absolute bottom-24 left-6">
        <div className="hud-label">VELOCITY</div>
        <div className="mt-1.5 space-y-1">
          {/* β bar */}
          <div>
            <div className="flex justify-between text-[11px]">
              <span className="text-text-dim">β</span>
              <span className="text-amber font-bold tabular-nums">
                {beta.toFixed(6)} c
              </span>
            </div>
            <div className="mt-0.5 h-1 w-full overflow-hidden bg-black/50">
              <div
                className="h-full bg-gradient-to-r from-amber/50 to-amber transition-all duration-150"
                style={{ width: `${beta * 100}%` }}
              />
            </div>
          </div>

          <div className="flex justify-between text-[11px]">
            <span className="text-text-dim">γ</span>
            <span className="text-amber tabular-nums">{gamma.toFixed(4)}</span>
          </div>

          <div className="flex justify-between text-[11px]">
            <span className="text-text-dim">v</span>
            <span className="text-text tabular-nums">
              {formatSpeed(speedKms)} km/s
            </span>
          </div>

          <div className="flex justify-between text-[11px]">
            <span className="text-text-dim">%c</span>
            <span className="text-text tabular-nums">{betaPct}%</span>
          </div>

          <div className="flex justify-between text-[11px]">
            <span className="text-text-dim">φ</span>
            <span className="text-text tabular-nums">{rapidity.toFixed(4)}</span>
          </div>
        </div>
      </div>

      {/* Energy Tax — below velocity */}
      <div className="hud-panel absolute bottom-6 left-6">
        <div className="hud-label">ENERGY TAX</div>
        <div className="mt-1 space-y-0.5">
          <div className={`text-lg font-bold tabular-nums ${energyClass(energyJoules)}`}>
            {energy.value}
            <span className="text-text-dim ml-1 text-xs font-normal">{energy.unit}</span>
          </div>
          {scale && (
            <div className={`text-[10px] tabular-nums ${energyClass(energyJoules)}`}>
              {scale}
            </div>
          )}
        </div>
      </div>

      {/* === RIGHT COLUMN (bottom area) === */}

      {/* Right side: Doppler readout */}
      <div className="hud-panel absolute top-24 right-6 text-right">
        <div className="hud-label">DOPPLER</div>
        <div className="mt-1.5 space-y-1.5">
          <div>
            <div className="flex items-baseline justify-between gap-3 text-[11px]">
              <span className="text-text-dim">FWD</span>
              <span className="tabular-nums font-bold" style={{ color: dopplerBandColor(fwdBand) }}>
                D={dopplerForward.toFixed(3)}
              </span>
            </div>
            <div className="text-right text-[9px] tracking-wider" style={{ color: dopplerBandColor(fwdBand) }}>
              {fwdBand}
            </div>
          </div>
          <div>
            <div className="flex items-baseline justify-between gap-3 text-[11px]">
              <span className="text-text-dim">AFT</span>
              <span className="tabular-nums font-bold" style={{ color: dopplerBandColor(aftBand) }}>
                D={dopplerAft.toFixed(3)}
              </span>
            </div>
            <div className="text-right text-[9px] tracking-wider" style={{ color: dopplerBandColor(aftBand) }}>
              {aftBand}
            </div>
          </div>
        </div>
      </div>

      {/* Proper acceleration gauge — only visible when thrusting */}
      {isThrusting && accelG > 0 && (
        <div className="hud-panel absolute right-6" style={{ top: "12.5rem" }}>
          <div className="hud-label">THRUST</div>
          <div className="mt-1">
            <div className="text-amber text-xl font-bold tabular-nums">
              {accelG.toFixed(2)}
              <span className="text-amber/50 ml-1 text-xs font-normal">g</span>
            </div>
            {/* g-bar */}
            <div className="mt-1 h-1 w-full overflow-hidden bg-black/50">
              <div
                className="h-full transition-all duration-150"
                style={{
                  width: `${Math.min(accelG / 10, 1) * 100}%`,
                  background: accelG > 5
                    ? "linear-gradient(90deg, #f59e0b, #ef4444)"
                    : "linear-gradient(90deg, #f59e0b80, #f59e0b)",
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Bottom-right: Navigation */}
      <div className="hud-panel absolute right-6 bottom-6 text-right">
        <div className="hud-label">NAVIGATION</div>
        <div className="mt-1.5 space-y-1">
          <div className="flex items-baseline justify-between gap-4 text-[11px]">
            <span className="text-text-dim">Earth</span>
            <span className="text-blue font-bold tabular-nums">
              {distanceToEarth.toFixed(3)} AU
            </span>
          </div>
          <div className="flex items-baseline justify-between gap-4 text-[11px]">
            <span className="text-text-dim" />
            <span className="text-text-dim tabular-nums">
              {(distanceToEarth * 149_597_870.7 / 1000).toFixed(0)}k km
            </span>
          </div>
          <div className="flex items-baseline justify-between gap-4 text-[11px]">
            <span className="text-text-dim">Light delay</span>
            <span className="text-text-dim tabular-nums">
              {(lightDelaySeconds / 60).toFixed(1)} min
            </span>
          </div>
          <div className="flex items-baseline justify-between gap-4 text-[11px]">
            <span className="text-text-dim">Apparent lag</span>
            <span className="text-amber tabular-nums">
              {lightDelaySeconds > 3600
                ? `${(lightDelaySeconds / 3600).toFixed(1)} hr`
                : `${(lightDelaySeconds / 60).toFixed(1)} min`}
            </span>
          </div>

          {/* Nav-Computer callout */}
          {nearTurnaround && phase !== "TURNAROUND" && (
            <div className="text-amber hud-warning mt-2 border-t border-amber/30 pt-2 text-[11px] font-bold tracking-wider">
              ▲ PREPARE TO TURN
            </div>
          )}
          {phase === "TURNAROUND" && (
            <div className="text-amber mt-2 border-t border-amber/30 pt-2 text-[11px] font-bold tracking-wider">
              ⟳ EXECUTING TURNAROUND
            </div>
          )}
        </div>
      </div>

      {/* Bottom center: β gauge */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2">
        <div className="flex items-center gap-2">
          <span className="text-text-dim text-[10px]">0</span>
          <div className="h-1.5 w-48 overflow-hidden rounded-full bg-black/40">
            <div
              className="h-full rounded-full transition-all duration-150"
              style={{
                width: `${beta * 100}%`,
                background: `linear-gradient(90deg, #06b6d4, #f59e0b ${Math.min(beta * 150, 100)}%, #ef4444)`,
              }}
            />
          </div>
          <span className="text-text-dim text-[10px]">c</span>
        </div>
      </div>
    </div>
  );
}
