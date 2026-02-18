"""Physics consistency checks: subluminal, causal, conservation, and arrival validation."""

import numpy as np
from numpy.typing import NDArray

from marte.trajectory import Worldline


def check_subluminal(worldline: Worldline) -> bool:
    """Verify that the ship speed is strictly less than c at every point on the worldline.

    Args:
        worldline: A ship Worldline.

    Returns:
        True if all velocities are subluminal.
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
