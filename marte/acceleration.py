"""Hyperbolic motion primitives for constant proper acceleration trajectories.

All functions implement the relativistic equations of motion for a uniformly
accelerated observer (Rindler coordinates → Minkowski mapping):

    x(τ) = (c²/a)(cosh(aτ/c) − 1)
    t(τ) = (c/a) sinh(aτ/c)
    β(τ) = tanh(aτ/c)
    γ(τ) = cosh(aτ/c)
    φ(τ) = aτ/c           (rapidity, linear in proper time)

Reference: Misner, Thorne & Wheeler, §6.
"""

from math import cosh, sinh, tanh

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT


def hyperbolic_position(proper_time: float, proper_accel: float) -> float:
    """Displacement along thrust axis for constant proper acceleration.

    x(τ) = (c²/a)(cosh(aτ/c) − 1)

    Args:
        proper_time: Proper time elapsed τ (s).
        proper_accel: Proper acceleration a (m/s²).

    Returns:
        Displacement x (m) along thrust direction.
    """
    return (c**2 / proper_accel) * (cosh(proper_accel * proper_time / c) - 1.0)


def hyperbolic_coord_time(proper_time: float, proper_accel: float) -> float:
    """Coordinate time elapsed for constant proper acceleration.

    t(τ) = (c/a) sinh(aτ/c)

    Args:
        proper_time: Proper time elapsed τ (s).
        proper_accel: Proper acceleration a (m/s²).

    Returns:
        Coordinate time t (s).
    """
    return (c / proper_accel) * sinh(proper_accel * proper_time / c)


def hyperbolic_beta(proper_time: float, proper_accel: float) -> float:
    """Speed as fraction of c for constant proper acceleration.

    β(τ) = tanh(aτ/c)

    Args:
        proper_time: Proper time elapsed τ (s).
        proper_accel: Proper acceleration a (m/s²).

    Returns:
        β = v/c (dimensionless).
    """
    return tanh(proper_accel * proper_time / c)


def hyperbolic_gamma(proper_time: float, proper_accel: float) -> float:
    """Lorentz factor for constant proper acceleration.

    γ(τ) = cosh(aτ/c)

    Args:
        proper_time: Proper time elapsed τ (s).
        proper_accel: Proper acceleration a (m/s²).

    Returns:
        Lorentz factor γ (dimensionless).
    """
    return cosh(proper_accel * proper_time / c)


def hyperbolic_rapidity(proper_time: float, proper_accel: float) -> float:
    """Rapidity for constant proper acceleration.

    φ(τ) = aτ/c

    Rapidity grows linearly with proper time — the natural parameter
    for uniformly accelerated motion.

    Args:
        proper_time: Proper time elapsed τ (s).
        proper_accel: Proper acceleration a (m/s²).

    Returns:
        Rapidity φ (dimensionless).
    """
    return proper_accel * proper_time / c


def build_acceleration_phase(
    proper_accel: float,
    tau_duration: float,
    n_points: int,
    direction: NDArray[np.float64],
    start_position: NDArray[np.float64],
    start_coord_time: float,
    start_proper_time: float,
    start_rapidity: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Build one phase of constant proper acceleration along a fixed direction.

    The phase starts from an existing rapidity (allowing smooth continuation
    from a previous phase). The sign of proper_accel determines whether the
    ship accelerates (+) or decelerates (−) along the direction vector.

    Args:
        proper_accel: Signed proper acceleration (m/s²). Positive = accelerate
            along direction, negative = decelerate.
        tau_duration: Proper time duration of this phase (s).
        n_points: Number of sample points (including endpoints).
        direction: Unit direction vector, shape (3,).
        start_position: Position at start of phase (m), shape (3,).
        start_coord_time: Coordinate time at start (s).
        start_proper_time: Proper time at start (s).
        start_rapidity: Rapidity at start (dimensionless). Sign convention:
            positive = moving along direction.

    Returns:
        Tuple of (coord_times, positions, proper_times, betas), each shape (n_points,)
        or (n_points, 3) for positions.
    """
    direction = np.asarray(direction, dtype=np.float64)
    start_position = np.asarray(start_position, dtype=np.float64)

    tau_samples = np.linspace(0.0, tau_duration, n_points)

    coord_times = np.empty(n_points)
    positions = np.empty((n_points, 3))
    proper_times = np.empty(n_points)
    betas = np.empty(n_points)

    # Precompute initial velocity-derived quantities for integration
    # The rapidity at time τ within this phase:
    #   φ(τ) = start_rapidity + a*τ/c
    # Velocity: β(τ) = tanh(φ(τ))
    # Position displacement: integral of c*tanh(φ) dt, but we need to be careful
    # with the relativistic kinematics.
    #
    # For a phase starting with rapidity φ₀:
    #   Δt(τ) = (c/a)[sinh(φ₀ + aτ/c) − sinh(φ₀)]
    #   Δx(τ) = (c²/a)[cosh(φ₀ + aτ/c) − cosh(φ₀)]
    #
    # where a is the proper acceleration (signed).

    a = proper_accel

    if abs(a) < 1e-20:
        # Zero acceleration: coast at current rapidity
        beta_const = np.tanh(start_rapidity)
        gamma_const = np.cosh(start_rapidity)
        for i, tau in enumerate(tau_samples):
            dt = tau * gamma_const  # dt = γ dτ for constant velocity
            coord_times[i] = start_coord_time + dt
            positions[i] = start_position + direction * beta_const * c * dt
            proper_times[i] = start_proper_time + tau
            betas[i] = abs(beta_const)
    else:
        phi_0 = start_rapidity
        sinh_phi0 = np.sinh(phi_0)
        cosh_phi0 = np.cosh(phi_0)

        for i, tau in enumerate(tau_samples):
            phi = phi_0 + a * tau / c
            sinh_phi = np.sinh(phi)
            cosh_phi = np.cosh(phi)

            # Coordinate time increment: Δt = (c/a)[sinh(φ) − sinh(φ₀)]
            dt = (c / a) * (sinh_phi - sinh_phi0)
            coord_times[i] = start_coord_time + dt

            # Position displacement along direction: Δx = (c²/a)[cosh(φ) − cosh(φ₀)]
            dx = (c**2 / a) * (cosh_phi - cosh_phi0)
            positions[i] = start_position + direction * dx

            proper_times[i] = start_proper_time + tau
            betas[i] = abs(np.tanh(phi))

    return coord_times, positions, proper_times, betas


def build_brachistochrone_worldline(
    proper_accel: float,
    tau_accel_out: float,
    tau_decel_out: float,
    tau_accel_in: float,
    tau_decel_in: float,
    direction_out: NDArray[np.float64],
    direction_in: NDArray[np.float64],
    start_position: NDArray[np.float64],
    start_coord_time: float,
    n_points_per_phase: int = 50,
) -> Worldline:
    """Build a 4-phase brachistochrone worldline with constant proper acceleration.

    Phases:
        1. Accelerate outbound (+a along direction_out)
        2. Decelerate outbound (−a along direction_out) → zero velocity at turnaround
        3. Accelerate inbound (+a along direction_in)
        4. Decelerate inbound (−a along direction_in) → zero velocity at arrival

    Args:
        proper_accel: Magnitude of proper acceleration (m/s²), always positive.
        tau_accel_out: Proper time for outbound acceleration phase (s).
        tau_decel_out: Proper time for outbound deceleration phase (s).
        tau_accel_in: Proper time for inbound acceleration phase (s).
        tau_decel_in: Proper time for inbound deceleration phase (s).
        direction_out: Outbound unit direction vector, shape (3,).
        direction_in: Inbound unit direction vector, shape (3,).
        start_position: Departure position (m), shape (3,).
        start_coord_time: Departure coordinate time (s).
        n_points_per_phase: Samples per phase.

    Returns:
        A Worldline with 4 * n_points_per_phase - 3 waypoints (boundaries shared).
    """
    direction_out = np.asarray(direction_out, dtype=np.float64)
    direction_in = np.asarray(direction_in, dtype=np.float64)
    start_position = np.asarray(start_position, dtype=np.float64)

    all_coord_times = []
    all_positions = []
    all_proper_times = []
    all_betas = []

    pos = start_position.copy()
    t_coord = start_coord_time
    tau = 0.0
    rapidity = 0.0

    phases = [
        (proper_accel, tau_accel_out, direction_out),    # Phase 1: accel out
        (-proper_accel, tau_decel_out, direction_out),   # Phase 2: decel out
        (proper_accel, tau_accel_in, direction_in),      # Phase 3: accel in
        (-proper_accel, tau_decel_in, direction_in),     # Phase 4: decel in
    ]

    for phase_idx, (accel, tau_dur, direction) in enumerate(phases):
        ct, ps, pt, bs = build_acceleration_phase(
            proper_accel=accel,
            tau_duration=tau_dur,
            n_points=n_points_per_phase,
            direction=direction,
            start_position=pos,
            start_coord_time=t_coord,
            start_proper_time=tau,
            start_rapidity=rapidity,
        )

        # Skip the first point for phases after the first (avoid duplicate boundary)
        if phase_idx > 0:
            ct = ct[1:]
            ps = ps[1:]
            pt = pt[1:]
            bs = bs[1:]

        all_coord_times.append(ct)
        all_positions.append(ps)
        all_proper_times.append(pt)
        all_betas.append(bs)

        # Update state for next phase
        rapidity = rapidity + accel * tau_dur / c
        pos = all_positions[-1][-1].copy()
        t_coord = all_coord_times[-1][-1]
        tau = all_proper_times[-1][-1]

    return Worldline(
        coord_times=np.concatenate(all_coord_times),
        positions=np.concatenate(all_positions),
        proper_times=np.concatenate(all_proper_times),
    )
