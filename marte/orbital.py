"""Earth position and velocity models in the Solar System Barycentric Inertial Frame."""

from __future__ import annotations

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

# Cached ephemeris for "ephemeris" earth model
_cached_ephemeris: object | None = None
_cached_ephemeris_range: tuple[float, float] | None = None


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


def _resolve_earth_model(elliptical: bool, earth_model: str | None) -> str:
    """Resolve the earth model string from legacy and new parameters.

    Priority: earth_model string > elliptical bool > default "circular".
    """
    if earth_model is not None:
        return earth_model
    if elliptical:
        return "elliptical"
    return "circular"


def _get_ephemeris_position(coord_time: float) -> NDArray[np.float64]:
    """Get Earth position from cached JPL Horizons ephemeris."""
    global _cached_ephemeris
    if _cached_ephemeris is None:
        raise RuntimeError(
            "Ephemeris data not loaded. Call load_ephemeris() or use "
            "earth_model='circular' or 'elliptical' instead."
        )
    return _cached_ephemeris.position(coord_time)  # type: ignore[union-attr]


def _get_ephemeris_velocity(coord_time: float) -> NDArray[np.float64]:
    """Get Earth velocity from cached JPL Horizons ephemeris."""
    global _cached_ephemeris
    if _cached_ephemeris is None:
        raise RuntimeError(
            "Ephemeris data not loaded. Call load_ephemeris() or use "
            "earth_model='circular' or 'elliptical' instead."
        )
    return _cached_ephemeris.velocity(coord_time)  # type: ignore[union-attr]


def load_ephemeris(t_start_s: float, t_end_s: float, step_days: int = 1) -> None:
    """Pre-load Earth ephemeris for use with earth_model='ephemeris'.

    Args:
        t_start_s: Start time in MARTE seconds since J2000.0.
        t_end_s: End time in MARTE seconds since J2000.0.
        step_days: Time step in days.
    """
    global _cached_ephemeris, _cached_ephemeris_range
    from marte.ephemeris import fetch_earth_ephemeris
    _cached_ephemeris = fetch_earth_ephemeris(t_start_s, t_end_s, step_days)
    _cached_ephemeris_range = (t_start_s, t_end_s)


def set_ephemeris(ephemeris_data: object) -> None:
    """Inject ephemeris data directly (for testing or pre-fetched data)."""
    global _cached_ephemeris
    _cached_ephemeris = ephemeris_data


def earth_position(
    coord_time: float,
    elliptical: bool = False,
    earth_model: str | None = None,
) -> NDArray[np.float64]:
    """Compute Earth's position vector at a given coordinate time.

    Args:
        coord_time: Coordinate time in SSBIF (s).
        elliptical: If True, use elliptical orbit with Kepler's equation.
            Default False preserves circular approximation.
        earth_model: Override model selection. One of:
            "circular" — analytical circular orbit (default)
            "elliptical" — Kepler equation
            "ephemeris" — JPL Horizons data (must call load_ephemeris first)

    Returns:
        Position vector [x, y, z] in meters, shape (3,).
    """
    model = _resolve_earth_model(elliptical, earth_model)
    if model == "ephemeris":
        return _get_ephemeris_position(coord_time)
    if model == "elliptical":
        return _earth_position_elliptical(coord_time)
    return _earth_position_circular(coord_time)


def earth_velocity(
    coord_time: float,
    elliptical: bool = False,
    earth_model: str | None = None,
) -> NDArray[np.float64]:
    """Compute Earth's velocity vector at a given coordinate time.

    Args:
        coord_time: Coordinate time in SSBIF (s).
        elliptical: If True, use elliptical orbit.
            Default False preserves circular approximation.
        earth_model: Override model selection (same as earth_position).

    Returns:
        Velocity vector [vx, vy, vz] in m/s, shape (3,).
    """
    model = _resolve_earth_model(elliptical, earth_model)
    if model == "ephemeris":
        return _get_ephemeris_velocity(coord_time)
    if model == "elliptical":
        return _earth_velocity_elliptical(coord_time)
    return _earth_velocity_circular(coord_time)
