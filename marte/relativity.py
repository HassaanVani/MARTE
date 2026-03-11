"""Relativistic kinematic primitives: Lorentz factor, proper time, energy, momentum, rapidity.

All β-based functions use the decomposition 1 - β² = (1 - β)(1 + β) to avoid
catastrophic cancellation at ultra-relativistic speeds (β → 1). Rapidity-based
alternatives are provided for computations that bypass β entirely.
"""

from math import atanh, cosh, log, sqrt, tanh

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT

c = SPEED_OF_LIGHT


def _one_minus_beta_sq(beta: float) -> float:
    """Compute 1 - β² as (1 - β)(1 + β) to avoid catastrophic cancellation.

    Direct computation of 1 - β² fails near β = 1 because β² ≈ 1 and the
    subtraction loses all significant digits. Factoring as (1 - β)(1 + β)
    preserves precision: (1 - β) is small but exact in floating point.
    """
    return (1.0 - beta) * (1.0 + beta)


def lorentz_factor(beta: float) -> float:
    """Compute the Lorentz factor γ = (1 - β²)^(-1/2).

    Uses the (1 - β)(1 + β) decomposition for numerical stability at β → 1.

    Args:
        beta: Speed as a fraction of c (v/c). Must satisfy 0 <= beta < 1.

    Returns:
        The Lorentz factor γ.
    """
    return 1.0 / sqrt(_one_minus_beta_sq(beta))


def lorentz_factor_from_rapidity(phi: float) -> float:
    """Compute the Lorentz factor from rapidity: γ = cosh(φ).

    Avoids β entirely — no cancellation possible. Preferred when rapidity
    is the natural parameter (e.g., constant proper acceleration).

    Args:
        phi: Rapidity (dimensionless).

    Returns:
        The Lorentz factor γ.
    """
    return cosh(phi)


def proper_time_elapsed(beta: float, coord_time_delta: float) -> float:
    """Compute proper time elapsed for a segment at constant β.

    Δτ = Δt / γ = Δt * √(1 - β²)

    Uses the (1 - β)(1 + β) decomposition for numerical stability at β → 1.

    Args:
        beta: Speed as a fraction of c.
        coord_time_delta: Coordinate time interval (s).

    Returns:
        Proper time elapsed (s).
    """
    return coord_time_delta * sqrt(_one_minus_beta_sq(beta))


def proper_time_from_rapidity(phi: float, coord_time_delta: float) -> float:
    """Compute proper time elapsed from rapidity: Δτ = Δt / cosh(φ).

    Avoids β entirely. Preferred for ultra-relativistic computations.

    Args:
        phi: Rapidity (dimensionless).
        coord_time_delta: Coordinate time interval (s).

    Returns:
        Proper time elapsed (s).
    """
    return coord_time_delta / cosh(phi)


def relativistic_kinetic_energy(beta: float, mass: float) -> float:
    """Compute relativistic kinetic energy E_k = (γ - 1)mc².

    Args:
        beta: Speed as a fraction of c.
        mass: Rest mass (kg).

    Returns:
        Kinetic energy (J).
    """
    return (lorentz_factor(beta) - 1.0) * mass * c**2


def kinetic_energy_from_rapidity(phi: float, mass: float) -> float:
    """Compute relativistic kinetic energy from rapidity: E_k = (cosh(φ) - 1)mc².

    Avoids β entirely. For extreme rapidity (φ >> 1), uses the identity
    cosh(φ) - 1 = 2 sinh²(φ/2) to avoid cancellation in cosh(φ) - 1.

    Args:
        phi: Rapidity (dimensionless).
        mass: Rest mass (kg).

    Returns:
        Kinetic energy (J).
    """
    # For large φ, cosh(φ) is huge and cosh(φ) - 1 ≈ cosh(φ), no issue.
    # For small φ, cosh(φ) ≈ 1 + φ²/2, so cosh(φ) - 1 ≈ φ²/2.
    # The identity 2sinh²(φ/2) handles both regimes well.
    from math import sinh
    gamma_minus_1 = 2.0 * sinh(phi / 2.0) ** 2
    return gamma_minus_1 * mass * c**2


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

    For β very close to 1, uses the identity arctanh(β) = ½ ln((1+β)/(1-β))
    which is more stable than the standard library arctanh.

    Args:
        beta: Speed as a fraction of c. Must satisfy 0 <= beta < 1.

    Returns:
        Rapidity (dimensionless).
    """
    if beta > 0.9999:
        # arctanh(β) = ½ ln((1+β)/(1-β)) — avoids internal 1-β² computation
        return 0.5 * log((1.0 + beta) / (1.0 - beta))
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
