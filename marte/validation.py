"""Physics consistency checks: subluminal, causal, conservation, and arrival validation."""

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT


def check_subluminal(worldline: Worldline) -> bool:
    """Verify that the ship speed is strictly less than c at every point on the worldline.

    Args:
        worldline: A ship Worldline.

    Returns:
        True if all velocities are subluminal.
    """
    for i in range(len(worldline.coord_times) - 1):
        dt = worldline.coord_times[i + 1] - worldline.coord_times[i]
        if dt <= 0:
            return False
        dr = worldline.positions[i + 1] - worldline.positions[i]
        speed = float(np.linalg.norm(dr)) / dt
        if speed >= c:
            return False
    return True


def check_proper_time_consistency(
    worldline: Worldline,
    expected_tau: float,
    rtol: float = 1e-9,
) -> bool:
    """Verify that the integrated proper time matches the expected value.

    Args:
        worldline: A ship Worldline.
        expected_tau: Expected total proper time (s).
        rtol: Relative tolerance for the comparison.

    Returns:
        True if |τ_computed - τ_expected| / τ_expected < rtol.
    """
    computed_tau = worldline.proper_times[-1]
    return abs(computed_tau - expected_tau) / expected_tau < rtol


def check_arrival_intersection(
    worldline: Worldline,
    earth_pos_at_tf: NDArray[np.float64],
    atol: float = 1.0,
) -> bool:
    """Verify that the ship's final position matches Earth's position at arrival time.

    Args:
        worldline: A ship Worldline.
        earth_pos_at_tf: Earth's position at arrival time (m), shape (3,).
        atol: Absolute tolerance in meters (default 1 m).

    Returns:
        True if |r_ship(t_f) - r_Earth(t_f)| < atol.
    """
    ship_final = worldline.positions[-1]
    distance = float(np.linalg.norm(ship_final - earth_pos_at_tf))
    return distance < atol
