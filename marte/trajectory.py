"""Ship worldline computation using piecewise constant-velocity trajectory model (v1)."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class Worldline:
    """A discretized ship worldline in SSBIF.

    Attributes:
        coord_times: Coordinate times at each waypoint (s), shape (N,).
        positions: Ship positions [x, y, z] at each waypoint (m), shape (N, 3).
        proper_times: Accumulated proper time at each waypoint (s), shape (N,).
    """

    coord_times: NDArray[np.float64]
    positions: NDArray[np.float64]
    proper_times: NDArray[np.float64]


def compute_ship_worldline(
    departure_time: float,
    turnaround_time: float,
    arrival_time: float,
    velocity_out: NDArray[np.float64],
    velocity_in: NDArray[np.float64],
) -> Worldline:
    """Compute the ship worldline for a piecewise constant-velocity trajectory.

    Version 1 model:
        Phase 1: Instantaneous acceleration at t_0 to velocity_out.
        Phase 2: Constant relativistic cruise (outbound) until t_turn.
        Phase 3: Instantaneous turnaround at t_turn.
        Phase 4: Constant relativistic cruise (inbound) until t_f.
        Phase 5: Instantaneous deceleration at t_f.

    Args:
        departure_time: Departure coordinate time t_0 (s).
        turnaround_time: Turnaround coordinate time t_turn (s).
        arrival_time: Arrival coordinate time t_f (s).
        velocity_out: Outbound velocity vector (m/s), shape (3,).
        velocity_in: Inbound velocity vector (m/s), shape (3,).

    Returns:
        The computed ship Worldline.
    """
    raise NotImplementedError
