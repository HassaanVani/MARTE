import type { InterpolatedState } from "../../types";

interface Props {
  interpolated: InterpolatedState | null;
}

const SPEED_OF_LIGHT_KMS = 299_792.458;

function formatSpeed(kms: number): string {
  if (kms < 1000) return kms.toFixed(1);
  if (kms < 1_000_000) return (kms / 1000).toFixed(1) + "k";
  return kms.toLocaleString("en", { maximumFractionDigits: 0 });
}

export function CockpitHUD({ interpolated }: Props) {
  if (!interpolated) return null;

  const { coordTime, properTime, beta, gamma, phase, distanceToEarth } =
    interpolated;

  const speedKms = beta * SPEED_OF_LIGHT_KMS;
  const timeDivergence = coordTime - properTime;
  const betaPct = (beta * 100).toFixed(1);

  return (
    <div className="hud-overlay pointer-events-none absolute inset-0 z-10">
      {/* Cockpit vignette */}
      <div className="cockpit-vignette absolute inset-0" />

      {/* Cockpit frame edges */}
      <div className="absolute inset-0">
        {/* Top edge */}
        <div className="absolute top-0 right-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-amber/20 to-transparent" />
        {/* Bottom edge */}
        <div className="absolute right-0 bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-amber/20 to-transparent" />
        {/* Corner brackets */}
        <div className="absolute top-3 left-3 h-6 w-6 border-t border-l border-amber/30" />
        <div className="absolute top-3 right-3 h-6 w-6 border-t border-r border-amber/30" />
        <div className="absolute bottom-3 left-3 h-6 w-6 border-b border-l border-amber/30" />
        <div className="absolute right-3 bottom-3 h-6 w-6 border-b border-r border-amber/30" />
      </div>

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
          <div className="text-amber mt-0.5 text-xs tabular-nums">
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

      {/* Center: Crosshair + velocity ring */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <svg width="120" height="120" viewBox="0 0 120 120" className="opacity-40">
          {/* Outer ring */}
          <circle cx="60" cy="60" r="50" stroke="#f59e0b" strokeWidth="0.5" fill="none" />
          {/* Tick marks */}
          <line x1="60" y1="6" x2="60" y2="14" stroke="#f59e0b" strokeWidth="1" />
          <line x1="60" y1="106" x2="60" y2="114" stroke="#f59e0b" strokeWidth="1" />
          <line x1="6" y1="60" x2="14" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <line x1="106" y1="60" x2="114" y2="60" stroke="#f59e0b" strokeWidth="1" />
          {/* Inner crosshair */}
          <line x1="60" y1="45" x2="60" y2="53" stroke="#f59e0b" strokeWidth="1" />
          <line x1="60" y1="67" x2="60" y2="75" stroke="#f59e0b" strokeWidth="1" />
          <line x1="45" y1="60" x2="53" y2="60" stroke="#f59e0b" strokeWidth="1" />
          <line x1="67" y1="60" x2="75" y2="60" stroke="#f59e0b" strokeWidth="1" />
          {/* Center dot */}
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

      {/* Bottom-left: Velocity panel */}
      <div className="hud-panel absolute bottom-6 left-6">
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
        </div>
      </div>

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
              {(distanceToEarth * 499.0 / 60).toFixed(1)} min
            </span>
          </div>
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
