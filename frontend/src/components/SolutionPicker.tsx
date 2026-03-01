import type { BranchData } from "../types";

interface Props {
  branches: BranchData[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

export function SolutionPicker({ branches, selectedIndex, onSelect }: Props) {
  if (branches.length <= 1) return null;

  return (
    <div className="flex items-center gap-2 border-t border-border px-4 py-2">
      <span className="text-text-dim text-[10px] tracking-wider uppercase">
        Branch
      </span>
      <div className="flex gap-1">
        {branches.map((_, i) => {
          const label = String.fromCharCode(65 + i); // A, B, C, ...
          const isSelected = i === selectedIndex;
          return (
            <button
              key={i}
              onClick={() => onSelect(i)}
              className={`h-6 w-6 text-xs font-bold transition-colors ${
                isSelected
                  ? "bg-amber text-bg border-amber border"
                  : "border-border text-text-dim hover:border-amber hover:text-amber border"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
