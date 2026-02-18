"""Earth position and velocity models in the Solar System Barycentric Inertial Frame."""

import numpy as np
from numpy.typing import NDArray

from marte.constants import EARTH_ORBITAL_ANGULAR_VEL, EARTH_ORBITAL_RADIUS

R = EARTH_ORBITAL_RADIUS
omega = EARTH_ORBITAL_ANGULAR_VEL


def earth_position(coord_time: float) -> NDArray[np.float64]:
    """Compute Earth's position vector at a given coordinate time.

    Version 1: Circular orbit approximation.
        r_E(t) = R * [cos(ωt), sin(ωt), 0]

    Args:
        coord_time: Coordinate time in SSBIF (s).

    Returns:
        Position vector [x, y, z] in meters, shape (3,).
    """
    angle = omega * coord_time
    return np.array([R * np.cos(angle), R * np.sin(angle), 0.0])


def earth_velocity(coord_time: float) -> NDArray[np.float64]:
    """Compute Earth's velocity vector at a given coordinate time.

    Version 1: Circular orbit approximation.
        v_E(t) = Rω * [-sin(ωt), cos(ωt), 0]

    Args:
        coord_time: Coordinate time in SSBIF (s).

    Returns:
        Velocity vector [vx, vy, vz] in m/s, shape (3,).
    """
    angle = omega * coord_time
    speed = R * omega
    return np.array([-speed * np.sin(angle), speed * np.cos(angle), 0.0])
