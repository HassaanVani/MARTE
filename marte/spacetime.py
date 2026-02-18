"""Minkowski interval computation, worldline utilities, and causal structure checks."""

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT


def minkowski_interval(
    event1: NDArray[np.float64],
    event2: NDArray[np.float64],
) -> float:
    """Compute the Minkowski spacetime interval between two events.

    ds² = -c²dt² + dx² + dy² + dz²

    Events are 4-vectors [t, x, y, z] with t in seconds and spatial components in meters.
    Timelike intervals are negative, spacelike are positive, null are zero.

    Args:
        event1: First event [t, x, y, z].
        event2: Second event [t, x, y, z].

    Returns:
        The spacetime interval ds² (m²). Negative for timelike separation.
    """
    d = np.asarray(event2, dtype=np.float64) - np.asarray(event1, dtype=np.float64)
    dt = d[0]
    dx = d[1:]
    return float(-c**2 * dt**2 + np.dot(dx, dx))


def is_timelike(interval: float) -> bool:
    """Check whether a Minkowski interval is timelike (ds² < 0).

    Args:
        interval: A spacetime interval ds².

    Returns:
        True if the interval is timelike.
    """
    return interval < 0


def is_causal(worldline: Worldline) -> bool:
    """Check whether a worldline is everywhere causal (timelike or null between successive events).

    Every consecutive pair of events on the worldline must have a timelike or null
    interval, i.e., the ship never exceeds the speed of light.

    Args:
        worldline: A ship Worldline.

    Returns:
        True if the worldline is causal.
    """
    for i in range(len(worldline.coord_times) - 1):
        event1 = np.array([
            worldline.coord_times[i],
            *worldline.positions[i],
        ])
        event2 = np.array([
            worldline.coord_times[i + 1],
            *worldline.positions[i + 1],
        ])
        interval = minkowski_interval(event1, event2)
        if interval > 0:  # spacelike → superluminal
            return False
    return True
