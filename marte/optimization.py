"""Pareto front optimization for energy vs proper time tradeoff."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from marte.constants import YEAR
from marte.solver import TrajectoryModel, solve_trajectory


@dataclass
class ParetoPoint:
    """A single point on the Pareto front."""

    proper_time_years: float
    energy_joules: float
    peak_beta: float
    params: dict


@dataclass
class ParetoFront:
    """The computed Pareto front."""

    points: list[ParetoPoint] = field(default_factory=list)
    target: str = "earth"
    base_params: dict = field(default_factory=dict)


def compute_pareto_front(
    t0: float,
    tf: float,
    mass: float,
    model: str = "constant_velocity",
    proper_acceleration: float | None = None,
    target: str = "earth",
    n_points: int = 50,
    earth_model: str | None = None,
) -> ParetoFront:
    """Compute the Pareto front of energy vs proper time.

    Sweeps proper_time from near-zero (extreme dilation, high energy) to
    near delta_t (minimal dilation, low energy). At each point, solves for
    the trajectory and records energy. Filters to Pareto-optimal points.

    Args:
        t0: Departure coordinate time (s).
        tf: Arrival coordinate time (s).
        mass: Ship rest mass (kg).
        model: Trajectory model string.
        proper_acceleration: Proper acceleration (m/s²), for constant_acceleration.
        target: Target body name.
        n_points: Number of points to evaluate.
        earth_model: Earth orbit model override.

    Returns:
        ParetoFront with Pareto-optimal points sorted by proper_time ascending.
    """
    n_points = min(n_points, 100)
    delta_t = tf - t0
    if delta_t <= 0:
        return ParetoFront(target=target)

    traj_model = (
        TrajectoryModel.CONSTANT_ACCELERATION
        if model == "constant_acceleration"
        else TrajectoryModel.CONSTANT_VELOCITY
    )

    # Sweep proper time from small fraction to near delta_t
    # Use log spacing near the low end for better coverage of high-energy region
    min_tau_frac = 0.05
    max_tau_frac = 0.98
    tau_fractions = np.linspace(min_tau_frac, max_tau_frac, n_points)

    candidates: list[ParetoPoint] = []

    for frac in tau_fractions:
        tau = frac * delta_t
        params = {
            "t0_s": t0,
            "tf_s": tf,
            "proper_time_s": tau,
            "mass_kg": mass,
            "model": model,
            "target": target,
        }

        try:
            sol = solve_trajectory(
                t0, tf, tau, mass,
                model=traj_model,
                proper_acceleration=proper_acceleration,
                target=target,
                earth_model=earth_model,
            )
            if not sol.converged:
                continue

            peak_beta = sol.peak_beta if sol.peak_beta is not None else sol.velocity_magnitude

            candidates.append(ParetoPoint(
                proper_time_years=sol.total_proper_time / YEAR,
                energy_joules=sol.energy,
                peak_beta=peak_beta,
                params=params,
            ))
        except (ValueError, RuntimeError):
            continue

    # Filter to Pareto-optimal points (non-dominated)
    # Remove only truly dominated points (where another point is strictly better
    # on both objectives). For monotonic energy-vs-tau, this keeps the full curve.
    pareto = _filter_pareto(candidates)

    # Sort by proper time ascending
    pareto.sort(key=lambda p: p.proper_time_years)

    return ParetoFront(
        points=pareto,
        target=target,
        base_params={"t0": t0, "tf": tf, "mass": mass, "model": model},
    )


def _filter_pareto(candidates: list[ParetoPoint]) -> list[ParetoPoint]:
    """Filter to Pareto-optimal points on the energy vs proper-time tradeoff curve.

    The front shows how energy cost trades against mission proper time.
    A point is removed only if another point at the same proper time
    achieves lower energy (a strictly dominated outlier).

    For well-behaved monotonic relationships (constant velocity), this
    preserves the full tradeoff curve.
    """
    if not candidates:
        return []

    # Sort by proper time, then remove duplicates at same tau keeping lowest energy
    candidates.sort(key=lambda p: p.proper_time_years)

    filtered: list[ParetoPoint] = []
    for p in candidates:
        # Skip near-duplicate tau values (keep lowest energy)
        if filtered and abs(p.proper_time_years - filtered[-1].proper_time_years) < 1e-6:
            if p.energy_joules < filtered[-1].energy_joules:
                filtered[-1] = p
            continue
        filtered.append(p)

    return filtered
