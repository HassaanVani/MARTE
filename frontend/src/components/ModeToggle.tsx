import type { ViewMode } from "../types";

interface Props {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export function ModeToggle({ mode, onChange }: Props) {
  return (
    <div className="flex gap-1">
      <button
        onClick={() => onChange("observer")}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold tracking-widest uppercase transition-colors ${
          mode === "observer"
            ? "bg-amber text-bg"
            : "text-text-dim hover:text-text border border-border hover:border-amber/50"
        }`}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" opacity="0.8">
          <circle cx="6" cy="6" r="2" />
          <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" strokeWidth="1" />
        </svg>
        Research
      </button>
      <button
        onClick={() => onChange("kinetic")}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold tracking-widest uppercase transition-colors ${
          mode === "kinetic"
            ? "bg-amber text-bg"
            : "text-text-dim hover:text-text border border-border hover:border-amber/50"
        }`}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" opacity="0.8">
          <polygon points="6,1 11,11 1,11" />
        </svg>
        Pilot
      </button>
    </div>
  );
}
