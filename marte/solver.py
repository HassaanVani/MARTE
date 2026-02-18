"""Constrained trajectory root-finding: solve for velocity, direction, and turnaround time."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from marte.trajectory import Worldline


@dataclass
class TrajectorySolution:
    """Result of the trajectory solver.

    Attributes:
        worldline: The computed ship worldline.
        velocity_magnitude: Required speed as fraction of c (beta).
        direction_out: Outbound unit direction vector, shape (3,).
        direction_in: Inbound unit direction vector, shape (3,).
        turnaround_time: Turnaround coordinate time (s).
        total_proper_time: Total proper time experienced by traveler (s).
        converged: Whether the solver converged.
        residual: Norm of the constraint residual vector.
    """

    worldline: Worldline
    velocity_magnitude: float
    direction_out: NDArray[np.float64]
    direction_in: NDArray[np.float64]
    turnaround_time: float
    total_proper_time: float
    converged: bool
    residual: float


def solve_trajectory(
    t0: float,
    tf: float,
    proper_time_desired: float,
) -> TrajectorySolution:
    """Solve for the trajectory matching departure, arrival, and proper time constraints.

    Finds velocity magnitude |v|, outbound direction d_out, and turnaround time t_turn
    such that:
        1. r_ship(t_f) = r_Earth(t_f)  (spatial intersection)
        2. τ_computed = τ_desired        (proper time match)
        3. |v| < c                       (subluminal bound)

    Uses SciPy nonlinear root-finding (4 unknowns, 4 equations).

    Args:
        t0: Departure coordinate time (s).
        tf: Arrival coordinate time (s).
        proper_time_desired: Desired traveler proper time (s).

    Returns:
        A TrajectorySolution with the computed trajectory and solver diagnostics.
    """
    raise NotImplementedError
