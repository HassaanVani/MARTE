"""Ship worldline computation using piecewise constant-velocity trajectory model (v1)."""

from dataclasses import dataclass
from math import sqrt

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT

c = SPEED_OF_LIGHT


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
    v_out = np.asarray(velocity_out, dtype=np.float64)
    v_in = np.asarray(velocity_in, dtype=np.float64)

    # Departure position (from Earth's position at t0)
    from marte.orbital import earth_position

    r_depart = earth_position(departure_time)

    # Outbound leg
    dt_out = turnaround_time - departure_time
    r_turn = r_depart + v_out * dt_out

    # Inbound leg
    dt_in = arrival_time - turnaround_time
    r_arrive = r_turn + v_in * dt_in

    # Compute beta for each leg
    speed_out = float(np.linalg.norm(v_out))
    speed_in = float(np.linalg.norm(v_in))
    beta_out = speed_out / c
    beta_in = speed_in / c

    # Proper time for each leg: Δτ = Δt * √(1 - β²)
    tau_out = dt_out * sqrt(1.0 - beta_out**2)
    tau_in = dt_in * sqrt(1.0 - beta_in**2)

    # Build waypoints: departure, turnaround, arrival
    coord_times = np.array([departure_time, turnaround_time, arrival_time])
    positions = np.array([r_depart, r_turn, r_arrive])
    proper_times = np.array([0.0, tau_out, tau_out + tau_in])

    return Worldline(
        coord_times=coord_times,
        positions=positions,
        proper_times=proper_times,
    )
