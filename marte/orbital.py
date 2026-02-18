"""Earth position and velocity models in the Solar System Barycentric Inertial Frame."""

import numpy as np
from numpy.typing import NDArray


def earth_position(coord_time: float) -> NDArray[np.float64]:
    """Compute Earth's position vector at a given coordinate time.

    Version 1: Circular orbit approximation.
        r_E(t) = R * [cos(ωt), sin(ωt), 0]

    Args:
        coord_time: Coordinate time in SSBIF (s).

    Returns:
        Position vector [x, y, z] in meters, shape (3,).
    """
    raise NotImplementedError


def earth_velocity(coord_time: float) -> NDArray[np.float64]:
    """Compute Earth's velocity vector at a given coordinate time.

    Version 1: Circular orbit approximation.
        v_E(t) = Rω * [-sin(ωt), cos(ωt), 0]

    Args:
        coord_time: Coordinate time in SSBIF (s).

    Returns:
        Velocity vector [vx, vy, vz] in m/s, shape (3,).
    """
    raise NotImplementedError
