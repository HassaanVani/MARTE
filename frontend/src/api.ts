import type { SolveParams, SolveResponse } from "./types";

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
