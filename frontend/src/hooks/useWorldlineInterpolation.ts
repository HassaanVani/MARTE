import { useMemo } from "react";
import type { EarthData, InterpolatedState, SolveResponse } from "../types";

/**
 * Binary search for the interval containing `target` in a sorted array.
 * Returns the index `i` such that arr[i] <= target < arr[i+1].
 */
function findInterval(arr: number[], target: number): number {
  let lo = 0;
  let hi = arr.length - 2;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (arr[mid]! <= target) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpPos(
  a: number[],
  b: number[],
  t: number,
): [number, number, number] {
  return [
    lerp(a[0]!, b[0]!, t),
    lerp(a[1]!, b[1]!, t),
    lerp(a[2]!, b[2]!, t),
  ];
}

function interpolateEarthPosition(
  earth: EarthData,
  coordTime: number,
): [number, number, number] {
  const times = earth.trajectory_times_years;
  const positions = earth.trajectory_positions_au;

  if (times.length === 0) return [1, 0, 0];

  if (coordTime <= times[0]!) {
    const p = positions[0]!;
    return [p[0]!, p[1]!, p[2]!];
  }
  if (coordTime >= times[times.length - 1]!) {
    const p = positions[positions.length - 1]!;
    return [p[0]!, p[1]!, p[2]!];
  }

  const i = findInterval(times, coordTime);
  const t0 = times[i]!;
  const t1 = times[i + 1]!;
  const frac = t1 > t0 ? (coordTime - t0) / (t1 - t0) : 0;
  return lerpPos(positions[i]!, positions[i + 1]!, frac);
}

function determinePhaseV1(
  progress: number,
): InterpolatedState["phase"] {
  // v1: constant velocity. 3 points: depart, turnaround, arrive
  // turnaround at midpoint
  if (progress < 0.5) return "ACCELERATING"; // outbound leg
  if (progress > 0.5) return "DECELERATING"; // inbound leg
  return "TURNAROUND";
}

function determinePhaseV2(
  coordTime: number,
  phaseBoundaries: number[],
): InterpolatedState["phase"] {
  // phase_boundaries_years: [t_accel_end, t_coast_end, t_decel_start, t_decel_end]
  // Or could be [t1, t2, t3, t4] for 4-phase brachistochrone
  if (phaseBoundaries.length >= 4) {
    if (coordTime < phaseBoundaries[0]!) return "ACCELERATING";
    if (coordTime < phaseBoundaries[1]!) return "COASTING";
    if (coordTime < phaseBoundaries[2]!) return "TURNAROUND";
    return "DECELERATING";
  }
  if (phaseBoundaries.length >= 2) {
    if (coordTime < phaseBoundaries[0]!) return "ACCELERATING";
    if (coordTime < phaseBoundaries[1]!) return "DECELERATING";
    return "DECELERATING";
  }
  return "ACCELERATING";
}

export function useWorldlineInterpolation(
  response: SolveResponse | null,
  progress: number,
): InterpolatedState | null {
  return useMemo(() => {
    if (
      !response?.solution ||
      !response.worldline ||
      !response.earth
    )
      return null;

    const { worldline, solution, earth } = response;
    const times = worldline.coord_times_years;
    const positions = worldline.positions_au;
    const properTimes = worldline.proper_times_years;
    const n = times.length;

    if (n < 2) return null;

    const tStart = times[0]!;
    const tEnd = times[n - 1]!;
    const coordTime = lerp(tStart, tEnd, progress);

    // Find interval and interpolation fraction
    const i = findInterval(times, coordTime);
    const t0 = times[i]!;
    const t1 = times[i + 1]!;
    const frac = t1 > t0 ? (coordTime - t0) / (t1 - t0) : 0;

    // Interpolate position
    const positionAU = lerpPos(positions[i]!, positions[i + 1]!, frac);

    // Interpolate proper time
    const properTime = lerp(properTimes[i]!, properTimes[i + 1]!, frac);

    // Beta
    let beta: number;
    if (worldline.beta_profile && worldline.beta_profile.length === n) {
      beta = lerp(worldline.beta_profile[i]!, worldline.beta_profile[i + 1]!, frac);
    } else {
      beta = solution.beta;
    }
    beta = Math.max(0, Math.min(beta, 0.9999));
    const gamma = 1 / Math.sqrt(1 - beta * beta);

    // Velocity direction: tangent along worldline
    const p0 = positions[i]!;
    const p1 = positions[i + 1]!;
    const dx = p1[0]! - p0[0]!;
    const dy = p1[1]! - p0[1]!;
    const dz = p1[2]! - p0[2]!;
    const dmag = Math.sqrt(dx * dx + dy * dy + dz * dz);
    const velocityDirection: [number, number, number] =
      dmag > 1e-12 ? [dx / dmag, dy / dmag, dz / dmag] : [1, 0, 0];

    // Phase
    const isV2 = solution.trajectory_model === "constant_acceleration";
    const phase = isV2 && solution.phase_boundaries_years
      ? determinePhaseV2(coordTime, solution.phase_boundaries_years)
      : determinePhaseV1(progress);

    // Earth position at current time
    const earthPositionAU = interpolateEarthPosition(earth, coordTime);

    // Distance to Earth
    const edx = positionAU[0] - earthPositionAU[0];
    const edy = positionAU[1] - earthPositionAU[1];
    const edz = positionAU[2] - earthPositionAU[2];
    const distanceToEarth = Math.sqrt(edx * edx + edy * edy + edz * edz);

    return {
      coordTime,
      properTime,
      positionAU,
      beta,
      gamma,
      velocityDirection,
      phase,
      distanceToEarth,
      earthPositionAU,
    };
  }, [response, progress]);
}
