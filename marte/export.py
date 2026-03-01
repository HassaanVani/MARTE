"""Export trajectory data as JSON and CSV."""

from __future__ import annotations

import csv
import io
import json

import numpy as np

from marte.constants import AU, YEAR
from marte.solver import TrajectorySolution


def export_json(solution: TrajectorySolution, params: dict) -> str:
    """Export full mission summary and worldline as a JSON string.

    Args:
        solution: The solved trajectory.
        params: Input parameters dict.

    Returns:
        JSON string with mission data.
    """
    report = export_mission_report(solution, params)
    return json.dumps(report, indent=2, default=_json_default)


def export_csv(solution: TrajectorySolution) -> str:
    """Export worldline as CSV.

    Columns: coord_time_s, proper_time_s, x_m, y_m, z_m, vx, vy, vz, beta, gamma

    Returns:
        CSV string.
    """
    wl = solution.worldline
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "coord_time_s", "proper_time_s",
        "x_m", "y_m", "z_m",
        "vx", "vy", "vz",
        "beta", "gamma",
    ])

    n = len(wl.coord_times)
    for i in range(n):
        t = float(wl.coord_times[i])
        tau = float(wl.proper_times[i])
        x, y, z = float(wl.positions[i][0]), float(wl.positions[i][1]), float(wl.positions[i][2])

        # Compute velocity from position differences
        if i < n - 1:
            dt = wl.coord_times[i + 1] - wl.coord_times[i]
            if dt > 0:
                dp = wl.positions[i + 1] - wl.positions[i]
                vx, vy, vz = float(dp[0] / dt), float(dp[1] / dt), float(dp[2] / dt)
            else:
                vx = vy = vz = 0.0
        else:
            # Last point: reuse previous velocity
            if n >= 2:
                dt = wl.coord_times[-1] - wl.coord_times[-2]
                if dt > 0:
                    dp = wl.positions[-1] - wl.positions[-2]
                    vx, vy, vz = float(dp[0] / dt), float(dp[1] / dt), float(dp[2] / dt)
                else:
                    vx = vy = vz = 0.0
            else:
                vx = vy = vz = 0.0

        from marte.constants import SPEED_OF_LIGHT
        speed = (vx**2 + vy**2 + vz**2) ** 0.5
        beta = speed / SPEED_OF_LIGHT
        gamma = 1.0 / (1.0 - beta**2) ** 0.5 if beta < 1.0 else float("inf")

        writer.writerow([t, tau, x, y, z, vx, vy, vz, beta, gamma])

    return output.getvalue()


def export_mission_report(solution: TrajectorySolution, params: dict) -> dict:
    """Build a structured mission report.

    Args:
        solution: The solved trajectory.
        params: Input parameters dict.

    Returns:
        Dict with inputs, results, worldline, and diagnostics.
    """
    wl = solution.worldline
    report: dict = {
        "inputs": params,
        "results": {
            "converged": solution.converged,
            "residual": solution.residual,
            "velocity_magnitude_beta": solution.velocity_magnitude,
            "total_proper_time_s": solution.total_proper_time,
            "total_proper_time_years": solution.total_proper_time / YEAR,
            "turnaround_time_s": solution.turnaround_time,
            "turnaround_time_years": solution.turnaround_time / YEAR,
            "energy_joules": solution.energy,
            "trajectory_model": solution.trajectory_model.value,
            "direction_out": solution.direction_out.tolist(),
            "direction_in": solution.direction_in.tolist(),
            "arrival_relative_velocity_m_s": solution.arrival_relative_velocity.tolist(),
        },
        "worldline": {
            "n_points": len(wl.coord_times),
            "coord_times_s": wl.coord_times.tolist(),
            "proper_times_s": wl.proper_times.tolist(),
            "positions_m": wl.positions.tolist(),
            "positions_au": (wl.positions / AU).tolist(),
        },
    }

    # v2 fields
    if solution.peak_beta is not None:
        report["results"]["peak_beta"] = solution.peak_beta
        report["results"]["peak_gamma"] = solution.peak_gamma
        report["results"]["proper_acceleration_m_s2"] = solution.proper_acceleration

    if solution.beta_profile:
        report["worldline"]["beta_profile"] = solution.beta_profile

    if solution.total_rapidity_change > 0:
        report["results"]["total_rapidity_change"] = solution.total_rapidity_change

    # GR diagnostics
    if solution.gr_diagnostics is not None:
        grd = solution.gr_diagnostics
        report["diagnostics"] = {
            "gr": {
                "sr_proper_time_s": grd.sr_proper_time_s,
                "gr_proper_time_s": grd.gr_proper_time_s,
                "delta_tau_s": grd.delta_tau_s,
                "relative_correction": grd.relative_correction,
            }
        }

    # Perturbation data
    if solution.perturbation is not None:
        pa = solution.perturbation
        diag = report.get("diagnostics", {})
        diag["perturbation"] = {
            "max_accel_sun_m_s2": pa.max_accel_sun,
            "max_accel_jupiter_m_s2": pa.max_accel_jupiter,
            "max_accel_saturn_m_s2": pa.max_accel_saturn,
        }
        report["diagnostics"] = diag

    return report


def _json_default(obj: object) -> object:
    """JSON serializer for numpy types."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
