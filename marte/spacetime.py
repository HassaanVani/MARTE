"""Minkowski interval computation, worldline utilities, and causal structure checks."""

import numpy as np
from numpy.typing import NDArray

from marte.trajectory import Worldline


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
    raise NotImplementedError


def is_timelike(interval: float) -> bool:
    """Check whether a Minkowski interval is timelike (ds² < 0).

    Args:
        interval: A spacetime interval ds².

    Returns:
        True if the interval is timelike.
    """
    raise NotImplementedError


def is_causal(worldline: Worldline) -> bool:
    """Check whether a worldline is everywhere causal (timelike or null between successive events).

    Every consecutive pair of events on the worldline must have a timelike or null
    interval, i.e., the ship never exceeds the speed of light.

    Args:
        worldline: A ship Worldline.

    Returns:
        True if the worldline is causal.
    """
    raise NotImplementedError
