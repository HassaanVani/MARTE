"""Multi-body gravitational perturbation analysis along worldlines.

Computes gravitational accelerations from Sun, Jupiter, and Saturn at each
point of a ship worldline, providing a perturbation budget.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from marte.constants import (
    GM_SUN,
    GRAVITATIONAL_CONSTANT,
    JUPITER_ORBITAL_ANGULAR_VEL,
    JUPITER_ORBITAL_RADIUS,
    M_JUPITER,
    M_SATURN,
    SATURN_ORBITAL_ANGULAR_VEL,
    SATURN_ORBITAL_RADIUS,
    STANDARD_GRAVITY,
)
from marte.trajectory import Worldline

# GM products (m³/s²)
GM_JUPITER = GRAVITATIONAL_CONSTANT * M_JUPITER
GM_SATURN = GRAVITATIONAL_CONSTANT * M_SATURN


def solar_gravitational_acceleration(position: NDArray[np.float64]) -> NDArray[np.float64]:
    """Gravitational acceleration from the Sun at a given position.

    Returns -GM_Sun/r³ × r (pointing toward Sun).
    """
    r = np.asarray(position, dtype=np.float64)
    r_mag = float(np.linalg.norm(r))
    if r_mag < 1.0:
        return np.zeros(3)
    return -GM_SUN / r_mag**3 * r


def planetary_position(body: str, t_s: float) -> NDArray[np.float64]:
    """Simple circular orbit position for Jupiter or Saturn at time t_s.

    Args:
        body: "jupiter" or "saturn"
        t_s: Coordinate time in seconds since J2000.0

    Returns:
        Position [x, y, z] in meters.
    """
    if body == "jupiter":
        angle = JUPITER_ORBITAL_ANGULAR_VEL * t_s
        return np.array([
            JUPITER_ORBITAL_RADIUS * np.cos(angle),
            JUPITER_ORBITAL_RADIUS * np.sin(angle),
            0.0,
        ])
    elif body == "saturn":
        angle = SATURN_ORBITAL_ANGULAR_VEL * t_s
        return np.array([
            SATURN_ORBITAL_RADIUS * np.cos(angle),
            SATURN_ORBITAL_RADIUS * np.sin(angle),
            0.0,
        ])
    else:
        raise ValueError(f"Unknown body: {body}")


def planetary_gravitational_acceleration(
    body: str,
    ship_position: NDArray[np.float64],
    t_s: float,
) -> NDArray[np.float64]:
    """Gravitational acceleration on ship from a planet.

    Args:
        body: "jupiter" or "saturn"
        ship_position: Ship position [x, y, z] in meters
        t_s: Coordinate time in seconds

    Returns:
        Acceleration vector in m/s².
    """
    planet_pos = planetary_position(body, t_s)
    r_vec = planet_pos - np.asarray(ship_position)
    r_mag = float(np.linalg.norm(r_vec))
    if r_mag < 1.0:
        return np.zeros(3)

    gm = GM_JUPITER if body == "jupiter" else GM_SATURN
    return gm / r_mag**3 * r_vec


@dataclass
class PerturbationAnalysis:
    """Results of multi-body gravitational perturbation analysis."""

    # Maximum acceleration magnitudes (m/s²)
    max_accel_sun: float
    max_accel_jupiter: float
    max_accel_saturn: float

    # Total impulse (Δv) from each body integrated along worldline (m/s)
    total_delta_v_sun: float
    total_delta_v_jupiter: float
    total_delta_v_saturn: float

    # Closest approach distances (m)
    closest_approach_sun: float
    closest_approach_jupiter: float
    closest_approach_saturn: float

    # Acceleration profiles (arrays of magnitudes at each worldline point)
    accel_profile_sun: list[float] | None = None
    accel_profile_jupiter: list[float] | None = None
    accel_profile_saturn: list[float] | None = None


def compute_perturbation_profile(worldline: Worldline) -> PerturbationAnalysis:
    """Compute gravitational perturbation from Sun, Jupiter, Saturn along a worldline.

    Returns a PerturbationAnalysis with acceleration profiles, maximum
    accelerations, integrated Δv, and closest approach distances.
    """
    ct = worldline.coord_times
    pos = worldline.positions
    n = len(ct)

    accel_sun = []
    accel_jupiter = []
    accel_saturn = []

    max_a_sun = 0.0
    max_a_jup = 0.0
    max_a_sat = 0.0

    dv_sun = 0.0
    dv_jup = 0.0
    dv_sat = 0.0

    min_r_sun = float("inf")
    min_r_jup = float("inf")
    min_r_sat = float("inf")

    for i in range(n):
        t = ct[i]
        p = pos[i]

        # Sun
        a_sun_vec = solar_gravitational_acceleration(p)
        a_sun_mag = float(np.linalg.norm(a_sun_vec))
        accel_sun.append(a_sun_mag)
        max_a_sun = max(max_a_sun, a_sun_mag)
        r_sun = float(np.linalg.norm(p))
        min_r_sun = min(min_r_sun, r_sun)

        # Jupiter
        a_jup_vec = planetary_gravitational_acceleration("jupiter", p, t)
        a_jup_mag = float(np.linalg.norm(a_jup_vec))
        accel_jupiter.append(a_jup_mag)
        max_a_jup = max(max_a_jup, a_jup_mag)
        jup_pos = planetary_position("jupiter", t)
        r_jup = float(np.linalg.norm(p - jup_pos))
        min_r_jup = min(min_r_jup, r_jup)

        # Saturn
        a_sat_vec = planetary_gravitational_acceleration("saturn", p, t)
        a_sat_mag = float(np.linalg.norm(a_sat_vec))
        accel_saturn.append(a_sat_mag)
        max_a_sat = max(max_a_sat, a_sat_mag)
        sat_pos = planetary_position("saturn", t)
        r_sat = float(np.linalg.norm(p - sat_pos))
        min_r_sat = min(min_r_sat, r_sat)

        # Integrate Δv: a * dt (trapezoidal for interior points)
        if i > 0:
            dt = ct[i] - ct[i - 1]
            dv_sun += 0.5 * (accel_sun[i - 1] + a_sun_mag) * dt
            dv_jup += 0.5 * (accel_jupiter[i - 1] + a_jup_mag) * dt
            dv_sat += 0.5 * (accel_saturn[i - 1] + a_sat_mag) * dt

    return PerturbationAnalysis(
        max_accel_sun=max_a_sun,
        max_accel_jupiter=max_a_jup,
        max_accel_saturn=max_a_sat,
        total_delta_v_sun=dv_sun,
        total_delta_v_jupiter=dv_jup,
        total_delta_v_saturn=dv_sat,
        closest_approach_sun=min_r_sun,
        closest_approach_jupiter=min_r_jup,
        closest_approach_saturn=min_r_sat,
        accel_profile_sun=accel_sun,
        accel_profile_jupiter=accel_jupiter,
        accel_profile_saturn=accel_saturn,
    )
