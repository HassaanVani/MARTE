"""Earth position and velocity models in the Solar System Barycentric Inertial Frame."""

import numpy as np
from numpy.typing import NDArray

from marte.constants import (
    EARTH_ECCENTRICITY,
    EARTH_ORBITAL_ANGULAR_VEL,
    EARTH_ORBITAL_RADIUS,
    EARTH_PERIHELION_LONGITUDE,
)

R = EARTH_ORBITAL_RADIUS  # semi-major axis for circular; used as 'a' for elliptical
omega = EARTH_ORBITAL_ANGULAR_VEL


def _earth_position_circular(coord_time: float) -> NDArray[np.float64]:
    """Circular orbit approximation: r_E(t) = R * [cos(ωt), sin(ωt), 0]."""
    angle = omega * coord_time
    return np.array([R * np.cos(angle), R * np.sin(angle), 0.0])


def _earth_velocity_circular(coord_time: float) -> NDArray[np.float64]:
    """Circular orbit velocity: v_E(t) = Rω * [-sin(ωt), cos(ωt), 0]."""
    angle = omega * coord_time
    speed = R * omega
    return np.array([-speed * np.sin(angle), speed * np.cos(angle), 0.0])


def _solve_kepler(mean_anomaly: float, eccentricity: float, tol: float = 1e-12) -> float:
    """Solve Kepler's equation M = E - e sin(E) via Newton-Raphson.

    Args:
        mean_anomaly: Mean anomaly M (radians).
        eccentricity: Orbital eccentricity e.
        tol: Convergence tolerance.

    Returns:
        Eccentric anomaly E (radians).
    """
    ecc_anom = mean_anomaly  # Initial guess
    for _ in range(50):
        d_ecc = (
            (ecc_anom - eccentricity * np.sin(ecc_anom) - mean_anomaly)
            / (1.0 - eccentricity * np.cos(ecc_anom))
        )
        ecc_anom -= d_ecc
        if abs(d_ecc) < tol:
            break
    return ecc_anom


def _true_anomaly_from_eccentric(ecc_anom: float, e: float) -> float:
    """Convert eccentric anomaly to true anomaly.

    ν = 2 arctan(√((1+e)/(1-e)) tan(E/2))
    """
    return 2.0 * np.arctan2(
        np.sqrt(1.0 + e) * np.sin(ecc_anom / 2.0),
        np.sqrt(1.0 - e) * np.cos(ecc_anom / 2.0),
    )


def _earth_position_elliptical(coord_time: float) -> NDArray[np.float64]:
    """Elliptical orbit using Kepler's equation.

    Uses semi-major axis a = EARTH_ORBITAL_RADIUS, eccentricity e, and
    longitude of perihelion ω_p.
    """
    e = EARTH_ECCENTRICITY
    a = R
    omega_p = EARTH_PERIHELION_LONGITUDE

    # Mean anomaly: M = n(t - t_perihelion)
    # For simplicity, t=0 corresponds to M=0 at perihelion
    mean_anom = omega * coord_time
    ecc_anom = _solve_kepler(mean_anom, e)
    nu = _true_anomaly_from_eccentric(ecc_anom, e)

    # Radius
    r = a * (1.0 - e * np.cos(ecc_anom))

    # Position in orbital plane (angle measured from perihelion direction)
    angle = nu + omega_p
    return np.array([r * np.cos(angle), r * np.sin(angle), 0.0])


def _earth_velocity_elliptical(coord_time: float) -> NDArray[np.float64]:
    """Elliptical orbit velocity via vis-viva and angular momentum."""
    e = EARTH_ECCENTRICITY
    a = R
    omega_p = EARTH_PERIHELION_LONGITUDE
    n = omega  # mean motion

    mean_anom = n * coord_time
    ecc_anom = _solve_kepler(mean_anom, e)
    nu = _true_anomaly_from_eccentric(ecc_anom, e)

    r = a * (1.0 - e * np.cos(ecc_anom))
    angle = nu + omega_p

    # dE/dt = n / (1 - e cos(E))
    decc_dt = n / (1.0 - e * np.cos(ecc_anom))

    # dν/dt = (1 + e cos(ν)) / (1 - e²) * (a/r)² * n... simplify via dE
    # Using: dr/dt and r dν/dt from orbital mechanics
    # vr = a e sin(E) dE/dt
    # vθ = a √(1-e²) cos(E) dE/dt ... wait, need perpendicular
    # Better: use Cartesian directly
    # x = r cos(angle), y = r sin(angle)
    # dx/dt = dr/dt cos(angle) - r sin(angle) dangle/dt
    # dr/dt = a e sin(E) dE/dt
    # dangle/dt = dν/dt (since omega_p is constant)
    # dν/dt from: r² dν/dt = na²√(1-e²)  (angular momentum)

    h = n * a**2 * np.sqrt(1.0 - e**2)  # specific angular momentum (m²/s)
    dnu_dt = h / r**2
    dr_dt = a * e * np.sin(ecc_anom) * decc_dt

    vx = dr_dt * np.cos(angle) - r * np.sin(angle) * dnu_dt
    vy = dr_dt * np.sin(angle) + r * np.cos(angle) * dnu_dt

    return np.array([vx, vy, 0.0])


def earth_position(coord_time: float, elliptical: bool = False) -> NDArray[np.float64]:
    """Compute Earth's position vector at a given coordinate time.

    Args:
        coord_time: Coordinate time in SSBIF (s).
        elliptical: If True, use elliptical orbit with Kepler's equation.
            Default False preserves circular approximation.

    Returns:
        Position vector [x, y, z] in meters, shape (3,).
    """
    if elliptical:
        return _earth_position_elliptical(coord_time)
    return _earth_position_circular(coord_time)


def earth_velocity(coord_time: float, elliptical: bool = False) -> NDArray[np.float64]:
    """Compute Earth's velocity vector at a given coordinate time.

    Args:
        coord_time: Coordinate time in SSBIF (s).
        elliptical: If True, use elliptical orbit.
            Default False preserves circular approximation.

    Returns:
        Velocity vector [vx, vy, vz] in m/s, shape (3,).
    """
    if elliptical:
        return _earth_velocity_elliptical(coord_time)
    return _earth_velocity_circular(coord_time)
