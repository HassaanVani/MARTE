"""Relativistic kinematic primitives: Lorentz factor, proper time, energy, momentum, rapidity."""


def lorentz_factor(beta: float) -> float:
    """Compute the Lorentz factor γ = (1 - β²)^(-1/2).

    Args:
        beta: Speed as a fraction of c (v/c). Must satisfy 0 <= beta < 1.

    Returns:
        The Lorentz factor γ.
    """
    raise NotImplementedError


def proper_time_elapsed(beta: float, coord_time_delta: float) -> float:
    """Compute proper time elapsed for a segment at constant β.

    Δτ = Δt / γ = Δt * √(1 - β²)

    Args:
        beta: Speed as a fraction of c.
        coord_time_delta: Coordinate time interval (s).

    Returns:
        Proper time elapsed (s).
    """
    raise NotImplementedError


def relativistic_kinetic_energy(beta: float, mass: float) -> float:
    """Compute relativistic kinetic energy E_k = (γ - 1)mc².

    Args:
        beta: Speed as a fraction of c.
        mass: Rest mass (kg).

    Returns:
        Kinetic energy (J).
    """
    raise NotImplementedError


def relativistic_momentum(beta: float, mass: float) -> float:
    """Compute relativistic momentum magnitude p = γmv = γmβc.

    Args:
        beta: Speed as a fraction of c.
        mass: Rest mass (kg).

    Returns:
        Momentum magnitude (kg·m/s).
    """
    raise NotImplementedError


def rapidity(beta: float) -> float:
    """Compute rapidity φ = arctanh(β).

    Rapidity is the natural parameter for Lorentz boosts. Unlike velocity,
    rapidities add linearly under composition of collinear boosts.

    Args:
        beta: Speed as a fraction of c. Must satisfy 0 <= beta < 1.

    Returns:
        Rapidity (dimensionless).
    """
    raise NotImplementedError


def beta_from_rapidity(rapidity_val: float) -> float:
    """Recover β from rapidity: β = tanh(φ).

    Args:
        rapidity_val: Rapidity (dimensionless).

    Returns:
        Speed as a fraction of c.
    """
    raise NotImplementedError
