import { useState } from "react";
import { exportCSV, exportJSON } from "../api";
import type { SolveParams, SolveResponse } from "../types";

interface Props {
  params: SolveParams;
  response: SolveResponse | null;
}

export function ExportPanel({ params, response }: Props) {
  const [exporting, setExporting] = useState<string | null>(null);
  const disabled = !response?.solution || !!response.error;

  const handleExport = async (format: "json" | "csv") => {
    setExporting(format);
    try {
      if (format === "json") {
        await exportJSON(params);
      } else {
        await exportCSV(params);
      }
    } catch {
      // Export failed silently
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex flex-col gap-2 p-4">
      <h2 className="text-amber text-xs font-bold tracking-widest uppercase">
        Export
      </h2>
      <div className="flex gap-2">
        <button
          onClick={() => handleExport("json")}
          disabled={disabled}
          className="border-border hover:border-amber hover:text-amber flex-1 border px-2 py-1.5 text-xs transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {exporting === "json" ? "Exporting..." : "Export JSON"}
        </button>
        <button
          onClick={() => handleExport("csv")}
          disabled={disabled}
          className="border-border hover:border-amber hover:text-amber flex-1 border px-2 py-1.5 text-xs transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {exporting === "csv" ? "Exporting..." : "Export CSV"}
        </button>
      </div>
    </div>
  );
}
