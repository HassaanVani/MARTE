import type { AnimationControls } from "../hooks/useAnimationState";
import type { InterpolatedState } from "../types";

interface Props {
  animation: AnimationControls;
  interpolated: InterpolatedState | null;
}

const SPEEDS = [1, 2, 5, 10];

export function TimelineControls({ animation, interpolated }: Props) {
  const { progress, playing, speed, play, pause, seek, setSpeed } = animation;

  return (
    <div className="timeline-bar flex items-center gap-4 border-t border-border bg-surface px-5 py-2.5">
      {/* Play/Pause */}
      <button
        onClick={playing ? pause : play}
        className="text-amber flex h-8 w-8 items-center justify-center border border-amber/30 hover:border-amber hover:bg-amber/10 transition-colors"
        title={playing ? "Pause" : "Play"}
      >
        {playing ? (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <rect x="2" y="1" width="3.5" height="12" rx="0.5" />
            <rect x="8.5" y="1" width="3.5" height="12" rx="0.5" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <polygon points="2,1 13,7 2,13" />
          </svg>
        )}
      </button>

      {/* Speed selector */}
      <div className="flex gap-0.5">
        {SPEEDS.map((s) => (
          <button
            key={s}
            onClick={() => setSpeed(s)}
            className={`px-2 py-1 text-[11px] font-bold transition-colors ${
              speed === s
                ? "bg-amber text-bg"
                : "text-text-dim hover:text-amber border border-transparent hover:border-amber/30"
            }`}
          >
            {s}x
          </button>
        ))}
      </div>

      {/* Coord time */}
      <div className="min-w-[110px]">
        <div className="text-text-dim text-[9px] tracking-wider uppercase">Earth time</div>
        <div className="text-text text-sm font-bold tabular-nums">
          {interpolated ? interpolated.coordTime.toFixed(4) : "—"}{" "}
          <span className="text-text-dim text-[10px] font-normal">yr</span>
        </div>
      </div>

      {/* Scrubber */}
      <div className="flex flex-1 flex-col gap-0.5">
        <input
          type="range"
          min={0}
          max={1}
          step={0.001}
          value={progress}
          onChange={(e) => seek(parseFloat(e.target.value))}
          className="timeline-scrubber"
        />
        {/* Progress percentage */}
        <div className="text-text-dim text-center text-[9px] tabular-nums">
          {(progress * 100).toFixed(1)}%
        </div>
      </div>

      {/* Phase label */}
      <div className="min-w-[130px] text-center">
        <div className="text-text-dim text-[9px] tracking-wider uppercase">Phase</div>
        <div className="text-amber text-sm font-bold tracking-wider">
          {interpolated?.phase ?? "—"}
        </div>
      </div>

      {/* Proper time */}
      <div className="min-w-[110px] text-right">
        <div className="text-text-dim text-[9px] tracking-wider uppercase">Ship time</div>
        <div className="text-cyan text-sm font-bold tabular-nums">
          {interpolated ? interpolated.properTime.toFixed(4) : "—"}{" "}
          <span className="text-cyan/50 text-[10px] font-normal">yr</span>
        </div>
      </div>
    </div>
  );
}
