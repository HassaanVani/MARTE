"""Relativistic kinematic primitives: Lorentz factor, proper time, energy, momentum, rapidity."""

from math import atanh, sqrt, tanh

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT

c = SPEED_OF_LIGHT


def lorentz_factor(beta: float) -> float:
    """Compute the Lorentz factor γ = (1 - β²)^(-1/2).

    Args:
        beta: Speed as a fraction of c (v/c). Must satisfy 0 <= beta < 1.

    Returns:
        The Lorentz factor γ.
    """
    return 1.0 / sqrt(1.0 - beta**2)


def proper_time_elapsed(beta: float, coord_time_delta: float) -> float:
    """Compute proper time elapsed for a segment at constant β.

    Δτ = Δt / γ = Δt * √(1 - β²)

    Args:
        beta: Speed as a fraction of c.
        coord_time_delta: Coordinate time interval (s).

    Returns:
        Proper time elapsed (s).
    """
    return coord_time_delta * sqrt(1.0 - beta**2)


def relativistic_kinetic_energy(beta: float, mass: float) -> float:
    """Compute relativistic kinetic energy E_k = (γ - 1)mc².

    Args:
        beta: Speed as a fraction of c.
        mass: Rest mass (kg).

    Returns:
        Kinetic energy (J).
    """
    return (lorentz_factor(beta) - 1.0) * mass * c**2


def relativistic_momentum(beta: float, mass: float) -> float:
    """Compute relativistic momentum magnitude p = γmv = γmβc.

    Args:
        beta: Speed as a fraction of c.
        mass: Rest mass (kg).

    Returns:
        Momentum magnitude (kg·m/s).
    """
    return lorentz_factor(beta) * mass * beta * c


def rapidity(beta: float) -> float:
    """Compute rapidity φ = arctanh(β).

    Rapidity is the natural parameter for Lorentz boosts. Unlike velocity,
    rapidities add linearly under composition of collinear boosts.

    Args:
        beta: Speed as a fraction of c. Must satisfy 0 <= beta < 1.

    Returns:
        Rapidity (dimensionless).
    """
    return atanh(beta)


def beta_from_rapidity(rapidity_val: float) -> float:
    """Recover β from rapidity: β = tanh(φ).

    Args:
        rapidity_val: Rapidity (dimensionless).

    Returns:
        Speed as a fraction of c.
    """
    return tanh(rapidity_val)


def relativistic_velocity_addition(
    v_object: NDArray[np.float64],
    v_frame: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Compute relativistic velocity addition (Einstein velocity addition formula).

    Transforms v_object from the original frame S into frame S' which moves at v_frame
    relative to S. This gives the velocity of the object as seen in the new frame.

    Args:
        v_object: Velocity of object in frame S (m/s), shape (3,).
        v_frame: Velocity of frame S' relative to S (m/s), shape (3,).

    Returns:
        Velocity of object in frame S' (m/s), shape (3,).
    """
    u = np.asarray(v_frame, dtype=np.float64)
    v = np.asarray(v_object, dtype=np.float64)
    u_mag = np.linalg.norm(u)

    if u_mag == 0.0:
        return v.copy()

    u_hat = u / u_mag
    gamma_u = 1.0 / sqrt(1.0 - (u_mag / c) ** 2)

    v_parallel = np.dot(v, u_hat) * u_hat
    v_perp = v - v_parallel

    denom = 1.0 - np.dot(v, u) / c**2
    v_prime_parallel = (v_parallel - u) / denom
    v_prime_perp = v_perp / (gamma_u * denom)

    return v_prime_parallel + v_prime_perp
