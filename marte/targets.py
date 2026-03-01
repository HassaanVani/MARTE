"""Registry of planetary targets with orbital parameters for multi-target missions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from marte.constants import (
    AU,
    EARTH_ORBITAL_ANGULAR_VEL,
    EARTH_ORBITAL_RADIUS,
    GRAVITATIONAL_CONSTANT,
    JUPITER_ORBITAL_ANGULAR_VEL,
    JUPITER_ORBITAL_RADIUS,
    M_JUPITER,
    M_MARS,
    M_MERCURY,
    M_VENUS,
    MARS_ORBITAL_ANGULAR_VEL,
    MARS_ORBITAL_RADIUS,
    MERCURY_ORBITAL_ANGULAR_VEL,
    MERCURY_ORBITAL_RADIUS,
    VENUS_ORBITAL_ANGULAR_VEL,
    VENUS_ORBITAL_RADIUS,
)


@dataclass
class CelestialTarget:
    """A planetary body that can serve as a mission target."""

    name: str
    orbital_radius_m: float
    orbital_angular_vel: float
    mass_kg: float | None = None
    gm: float | None = None

    @property
    def orbital_radius_au(self) -> float:
        return self.orbital_radius_m / AU


TARGETS: dict[str, CelestialTarget] = {
    "earth": CelestialTarget(
        name="Earth",
        orbital_radius_m=EARTH_ORBITAL_RADIUS,
        orbital_angular_vel=EARTH_ORBITAL_ANGULAR_VEL,
        mass_kg=5.972e24,
        gm=3.986e14,
    ),
    "mercury": CelestialTarget(
        name="Mercury",
        orbital_radius_m=MERCURY_ORBITAL_RADIUS,
        orbital_angular_vel=MERCURY_ORBITAL_ANGULAR_VEL,
        mass_kg=M_MERCURY,
        gm=GRAVITATIONAL_CONSTANT * M_MERCURY,
    ),
    "venus": CelestialTarget(
        name="Venus",
        orbital_radius_m=VENUS_ORBITAL_RADIUS,
        orbital_angular_vel=VENUS_ORBITAL_ANGULAR_VEL,
        mass_kg=M_VENUS,
        gm=GRAVITATIONAL_CONSTANT * M_VENUS,
    ),
    "mars": CelestialTarget(
        name="Mars",
        orbital_radius_m=MARS_ORBITAL_RADIUS,
        orbital_angular_vel=MARS_ORBITAL_ANGULAR_VEL,
        mass_kg=M_MARS,
        gm=GRAVITATIONAL_CONSTANT * M_MARS,
    ),
    "jupiter": CelestialTarget(
        name="Jupiter",
        orbital_radius_m=JUPITER_ORBITAL_RADIUS,
        orbital_angular_vel=JUPITER_ORBITAL_ANGULAR_VEL,
        mass_kg=M_JUPITER,
        gm=GRAVITATIONAL_CONSTANT * M_JUPITER,
    ),
}


def target_position(name: str, t_s: float) -> NDArray[np.float64]:
    """Compute target planet position at coordinate time t_s (circular orbit).

    Args:
        name: Target name (e.g. "mars", "earth").
        t_s: Coordinate time in seconds.

    Returns:
        Position vector [x, y, z] in meters, shape (3,).
    """
    tgt = TARGETS[name.lower()]
    angle = tgt.orbital_angular_vel * t_s
    r = tgt.orbital_radius_m
    return np.array([r * np.cos(angle), r * np.sin(angle), 0.0])


def target_velocity(name: str, t_s: float) -> NDArray[np.float64]:
    """Compute target planet velocity at coordinate time t_s (circular orbit).

    Args:
        name: Target name (e.g. "mars", "earth").
        t_s: Coordinate time in seconds.

    Returns:
        Velocity vector [vx, vy, vz] in m/s, shape (3,).
    """
    tgt = TARGETS[name.lower()]
    angle = tgt.orbital_angular_vel * t_s
    r = tgt.orbital_radius_m
    omega = tgt.orbital_angular_vel
    speed = r * omega
    return np.array([-speed * np.sin(angle), speed * np.cos(angle), 0.0])


def list_targets() -> list[str]:
    """Return list of available target names."""
    return list(TARGETS.keys())
