import type { AnimationControls } from "../../hooks/useAnimationState";
import type { InterpolatedState } from "../../types";

interface Props {
  animation: AnimationControls;
  interpolated: InterpolatedState | null;
}

/**
 * Diegetic cockpit timeline — the "Waiting Mechanic" from VISION.md.
 * Shows the Subjective Calendar (proper time) alongside the Home Calendar
 * (coordinate time) with a visual divergence bar.
 */
export function CockpitTimeline({ animation, interpolated }: Props) {
  if (!interpolated) return null;

  const { coordTime, properTime, gamma } = interpolated;
  const { progress } = animation;
  const divergence = coordTime - properTime;
  const dilationRate = gamma > 0 ? 1 / gamma : 1;

  return (
    <div className="pointer-events-none absolute right-0 bottom-0 left-0 z-10">
      <div className="mx-auto flex max-w-xl items-center gap-4 px-6 py-3">
        {/* Ship (Subjective) calendar */}
        <div className="flex-1 text-right">
          <div className="text-[8px] tracking-[0.2em] text-cyan/50 uppercase">
            Subjective
          </div>
          <div className="text-cyan text-lg font-bold tabular-nums">
            {properTime.toFixed(4)}
            <span className="text-cyan/40 ml-1 text-[10px] font-normal">yr</span>
          </div>
        </div>

        {/* Divergence bar */}
        <div className="flex w-32 flex-col items-center gap-1">
          {/* Time dilation rate indicator */}
          <div className="text-[8px] tabular-nums text-amber/60">
            dτ/dt = {dilationRate.toFixed(4)}
          </div>

          {/* Progress bar with divergence overlay */}
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-black/40">
            {/* Coordinate time progress (full bar) */}
            <div
              className="absolute top-0 left-0 h-full rounded-full bg-text/20 transition-all duration-100"
              style={{ width: `${progress * 100}%` }}
            />
            {/* Proper time progress (shorter bar, showing the dilation gap) */}
            <div
              className="absolute top-0 left-0 h-full rounded-full transition-all duration-100"
              style={{
                width: `${(progress * dilationRate) * 100}%`,
                background: "linear-gradient(90deg, #06b6d4, #06b6d480)",
              }}
            />
          </div>

          {/* Divergence */}
          {divergence > 0.001 && (
            <div className={`text-[8px] tabular-nums ${
              divergence > 0.5 ? "text-amber hud-warning" : "text-amber/60"
            }`}>
              Δ {divergence.toFixed(4)} yr lost
            </div>
          )}
        </div>

        {/* Earth (Home) calendar */}
        <div className="flex-1 text-left">
          <div className="text-[8px] tracking-[0.2em] text-text-dim/50 uppercase">
            Home
          </div>
          <div className="text-text text-lg font-bold tabular-nums">
            {coordTime.toFixed(4)}
            <span className="text-text-dim/40 ml-1 text-[10px] font-normal">yr</span>
          </div>
        </div>
      </div>
    </div>
  );
}
