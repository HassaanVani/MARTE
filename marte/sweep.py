"""Parameter sweep engine for batch trajectory solving."""

from __future__ import annotations

from dataclasses import dataclass, field

from marte.constants import STANDARD_GRAVITY, YEAR
from marte.solver import TrajectoryModel, solve_trajectory


@dataclass
class SweepPoint:
    """Result of a single sweep evaluation."""

    params: dict
    energy: float | None = None
    proper_time_s: float | None = None
    peak_beta: float | None = None
    converged: bool = False
    error: str | None = None


@dataclass
class Sweep1DResult:
    """Result of a 1D parameter sweep."""

    swept_param: str
    values: list[float]
    points: list[SweepPoint]


@dataclass
class Sweep2DResult:
    """Result of a 2D parameter sweep."""

    x_param: str
    y_param: str
    x_values: list[float]
    y_values: list[float]
    grid: list[list[SweepPoint]] = field(default_factory=list)


def _solve_point(params: dict, target: str = "earth") -> SweepPoint:
    """Solve a single trajectory point with error handling."""
    try:
        t0 = params.get("t0_years", 0.0) * YEAR
        tf = params["tf_years"] * YEAR
        tau = params["proper_time_years"] * YEAR
        mass = params.get("mass_kg", 1000.0)

        model_str = params.get("trajectory_model", "constant_velocity")
        model = (
            TrajectoryModel.CONSTANT_ACCELERATION
            if model_str == "constant_acceleration"
            else TrajectoryModel.CONSTANT_VELOCITY
        )

        proper_accel = None
        if model == TrajectoryModel.CONSTANT_ACCELERATION:
            accel_g = params.get("proper_acceleration_g", 1.0)
            proper_accel = accel_g * STANDARD_GRAVITY

        sol = solve_trajectory(
            t0, tf, tau, mass,
            model=model,
            proper_acceleration=proper_accel,
            target=target,
        )

        return SweepPoint(
            params=params,
            energy=sol.energy,
            proper_time_s=sol.total_proper_time,
            peak_beta=sol.peak_beta if sol.peak_beta is not None else sol.velocity_magnitude,
            converged=sol.converged,
        )
    except (ValueError, RuntimeError) as e:
        return SweepPoint(params=params, error=str(e))


def sweep_1d(
    base_params: dict,
    param_name: str,
    values: list[float],
    target: str = "earth",
) -> Sweep1DResult:
    """Sweep a single parameter over a range of values.

    Args:
        base_params: Base parameter dict (same keys as SolveRequest).
        param_name: Which parameter to sweep (e.g. "tf_years").
        values: List of values to evaluate.
        target: Target body name.

    Returns:
        Sweep1DResult with points for each value.
    """
    points = []
    for v in values:
        p = {**base_params, param_name: v}
        points.append(_solve_point(p, target))

    return Sweep1DResult(
        swept_param=param_name,
        values=values,
        points=points,
    )


def sweep_2d(
    base_params: dict,
    x_param: str,
    x_values: list[float],
    y_param: str,
    y_values: list[float],
    target: str = "earth",
) -> Sweep2DResult:
    """Sweep two parameters over a 2D grid.

    Args:
        base_params: Base parameter dict.
        x_param: X-axis parameter name.
        x_values: X-axis values.
        y_param: Y-axis parameter name.
        y_values: Y-axis values.
        target: Target body name.

    Returns:
        Sweep2DResult with grid[y][x] of SweepPoints.
    """
    grid = []
    for yv in y_values:
        row = []
        for xv in x_values:
            p = {**base_params, x_param: xv, y_param: yv}
            row.append(_solve_point(p, target))
        grid.append(row)

    return Sweep2DResult(
        x_param=x_param,
        y_param=y_param,
        x_values=x_values,
        y_values=y_values,
        grid=grid,
    )
