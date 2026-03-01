import type { ViewMode } from "../types";

interface Props {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

import type { ReactNode } from "react";

const MODES: { value: ViewMode; label: string; icon: ReactNode }[] = [
  {
    value: "observer",
    label: "Research",
    icon: (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" opacity="0.8">
        <circle cx="6" cy="6" r="2" />
        <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" strokeWidth="1" />
      </svg>
    ),
  },
  {
    value: "kinetic",
    label: "Pilot",
    icon: (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" opacity="0.8">
        <polygon points="6,1 11,11 1,11" />
      </svg>
    ),
  },
  {
    value: "planning",
    label: "Planning",
    icon: (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" opacity="0.8">
        <rect x="1" y="3" width="4" height="6" />
        <rect x="7" y="1" width="4" height="8" />
        <line x1="0" y1="11" x2="12" y2="11" stroke="currentColor" strokeWidth="1" />
      </svg>
    ),
  },
];

export function ModeToggle({ mode, onChange }: Props) {
  return (
    <div className="flex gap-1">
      {MODES.map((m) => (
        <button
          key={m.value}
          onClick={() => onChange(m.value)}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold tracking-widest uppercase transition-colors ${
            mode === m.value
              ? "bg-amber text-bg"
              : "text-text-dim hover:text-text border border-border hover:border-amber/50"
          }`}
        >
          {m.icon}
          {m.label}
        </button>
      ))}
    </div>
  );
}
