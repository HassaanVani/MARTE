import type {
  ParetoConfig,
  ParetoResult,
  SolveParams,
  SolveResponse,
  Sweep1DConfig,
  Sweep1DResult,
  Sweep2DConfig,
  Sweep2DResult,
  TargetInfoData,
} from "./types";

export async function solveTrajectory(
  params: SolveParams,
): Promise<SolveResponse> {
  const resp = await fetch("/api/solve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`);
  }
  return resp.json() as Promise<SolveResponse>;
}

export async function fetchTargets(): Promise<TargetInfoData[]> {
  const resp = await fetch("/api/targets");
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`);
  }
  return resp.json() as Promise<TargetInfoData[]>;
}

async function downloadFile(url: string, params: SolveParams, filename: string) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    throw new Error(`Export error: ${resp.status}`);
  }
  const blob = await resp.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export async function exportJSON(params: SolveParams): Promise<void> {
  await downloadFile("/api/export/json", params, "marte_trajectory.json");
}

export async function exportCSV(params: SolveParams): Promise<void> {
  await downloadFile("/api/export/csv", params, "marte_worldline.csv");
}

export async function sweep1D(
  baseParams: SolveParams,
  config: Sweep1DConfig,
): Promise<Sweep1DResult> {
  const resp = await fetch("/api/sweep/1d", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base_params: baseParams,
      param_name: config.param_name,
      min_value: config.min_value,
      max_value: config.max_value,
      steps: config.steps,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Sweep error: ${resp.status}`);
  }
  return resp.json() as Promise<Sweep1DResult>;
}

export async function sweep2D(
  baseParams: SolveParams,
  config: Sweep2DConfig,
): Promise<Sweep2DResult> {
  const resp = await fetch("/api/sweep/2d", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base_params: baseParams,
      x_param: config.x_param,
      x_min: config.x_min,
      x_max: config.x_max,
      y_param: config.y_param,
      y_min: config.y_min,
      y_max: config.y_max,
      x_steps: config.x_steps,
      y_steps: config.y_steps,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Sweep error: ${resp.status}`);
  }
  return resp.json() as Promise<Sweep2DResult>;
}

export async function computePareto(config: ParetoConfig): Promise<ParetoResult> {
  const resp = await fetch("/api/pareto", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!resp.ok) {
    throw new Error(`Pareto error: ${resp.status}`);
  }
  return resp.json() as Promise<ParetoResult>;
}
