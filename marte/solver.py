"""Trajectory solver — dispatches between v1 (constant velocity) and v2 (constant acceleration)."""

from dataclasses import dataclass, field
from enum import Enum
from math import acos, atan2, sqrt

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT
from marte.orbital import earth_position, earth_velocity
from marte.relativity import (
    relativistic_kinetic_energy,
    relativistic_velocity_addition,
)
from marte.trajectory import Worldline, compute_ship_worldline
from marte.validation import (
    check_arrival_intersection,
    check_proper_time_consistency,
    check_subluminal,
)

c = SPEED_OF_LIGHT


class TrajectoryModel(Enum):
    """Trajectory model selection."""

    CONSTANT_VELOCITY = "constant_velocity"
    CONSTANT_ACCELERATION = "constant_acceleration"


@dataclass
class TrajectorySolution:
    """Result of the trajectory solver.

    Attributes:
        worldline: The computed ship worldline.
        velocity_magnitude: Required speed as fraction of c (beta). For v2, this is the peak beta.
        direction_out: Outbound unit direction vector, shape (3,).
        direction_in: Inbound unit direction vector, shape (3,).
        turnaround_time: Turnaround coordinate time (s).
        total_proper_time: Total proper time experienced by traveler (s).
        converged: Whether the solver converged.
        residual: Norm of the constraint residual vector.
        energy: Required kinetic energy per leg (J).
        arrival_relative_velocity: Ship velocity relative to Earth at arrival (m/s), shape (3,).
        trajectory_model: Which model produced this solution.
        proper_acceleration: Proper acceleration (m/s²), None for v1.
        peak_beta: Peak speed as fraction of c, None for v1.
        peak_gamma: Peak Lorentz factor, None for v1.
        phase_boundaries: Coordinate times at phase boundaries (s), None for v1.
        beta_profile: β values at each worldline point, None for v1.
    """

    worldline: Worldline
    velocity_magnitude: float
    direction_out: NDArray[np.float64]
    direction_in: NDArray[np.float64]
    turnaround_time: float
    total_proper_time: float
    converged: bool
    residual: float
    energy: float
    arrival_relative_velocity: NDArray[np.float64]
    # v2 fields (optional, None for v1)
    trajectory_model: TrajectoryModel = TrajectoryModel.CONSTANT_VELOCITY
    proper_acceleration: float | None = None
    peak_beta: float | None = None
    peak_gamma: float | None = None
    phase_boundaries: list[float] = field(default_factory=list)
    beta_profile: list[float] = field(default_factory=list)


def solve_trajectory(
    t0: float,
    tf: float,
    proper_time_desired: float,
    mass: float = 1000.0,
    model: TrajectoryModel = TrajectoryModel.CONSTANT_VELOCITY,
    proper_acceleration: float | None = None,
) -> TrajectorySolution:
    """Solve for the trajectory matching departure, arrival, and proper time constraints.

    Dispatches to the appropriate solver based on the model parameter.

    Args:
        t0: Departure coordinate time (s).
        tf: Arrival coordinate time (s).
        proper_time_desired: Desired traveler proper time (s).
        mass: Ship rest mass in kg (default: 1000 kg).
        model: Trajectory model to use.
        proper_acceleration: Proper acceleration in m/s² (required for CONSTANT_ACCELERATION).

    Returns:
        A TrajectorySolution with the computed trajectory and solver diagnostics.
    """
    if model == TrajectoryModel.CONSTANT_ACCELERATION:
        from marte.solver_v2 import _solve_v2

        return _solve_v2(t0, tf, proper_time_desired, mass, proper_acceleration)

    return _solve_v1(t0, tf, proper_time_desired, mass)


def _solve_v1(
    t0: float,
    tf: float,
    proper_time_desired: float,
    mass: float = 1000.0,
) -> TrajectorySolution:
    """Analytical solver for the v1 piecewise constant-velocity model."""
    delta_t = tf - t0
    tau = proper_time_desired

    if delta_t <= 0:
        raise ValueError("Arrival time must be after departure time (tf > t0).")
    if tau <= 0:
        raise ValueError("Proper time must be positive.")
    if tau >= delta_t:
        raise ValueError(
            f"Proper time ({tau:.3e} s) must be less than coordinate time ({delta_t:.3e} s) "
            "for a relativistic trajectory."
        )

    # Step 1: Compute β analytically from proper time constraint
    # τ = Δt * √(1 - β²)  →  β = √(1 - (τ/Δt)²)
    ratio = tau / delta_t
    beta = sqrt(1.0 - ratio**2)

    # Step 2: Turnaround at midpoint
    t_turn = (t0 + tf) / 2.0

    # Step 3: Earth positions at departure and arrival
    r_e0 = earth_position(t0)
    r_ef = earth_position(tf)

    # Step 4: Displacement vector and its properties
    d = r_ef - r_e0
    d_mag = float(np.linalg.norm(d))
    alpha = atan2(float(d[1]), float(d[0]))

    # Step 5: Distances traveled on each leg
    speed = beta * c
    dt_out = t_turn - t0
    dt_in = tf - t_turn
    d_out = speed * dt_out
    d_in = speed * dt_in

    # Step 6: Law of cosines to find outbound direction
    # The triangle: departure → turnaround → arrival
    # Side lengths: d_out (departure to turn), d_in (turn to arrival), d_mag (departure to arrival)
    # cos(θ_out - α) = (d_out² + d_mag² - d_in²) / (2 · d_out · d_mag)
    if d_mag < 1e-6:
        # Earth barely moved — trajectory is essentially radial out-and-back
        theta_out = 0.0
    else:
        cos_arg = (d_out**2 + d_mag**2 - d_in**2) / (2.0 * d_out * d_mag)
        # Clamp for numerical safety
        cos_arg = max(-1.0, min(1.0, cos_arg))
        angle_offset = acos(cos_arg)
        theta_out = alpha + angle_offset  # First branch (above displacement vector)

    # Step 7: Build velocity vectors
    dir_out = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])
    v_out = speed * dir_out

    # Turnaround position
    r_turn = r_e0 + v_out * dt_out

    # Inbound direction: from turnaround to Earth at tf
    r_in_vec = r_ef - r_turn
    r_in_mag = float(np.linalg.norm(r_in_vec))
    if r_in_mag < 1e-6:
        dir_in = -dir_out
    else:
        dir_in = r_in_vec / r_in_mag

    v_in = speed * dir_in

    # Step 8: Compute worldline
    worldline = compute_ship_worldline(
        departure_time=t0,
        turnaround_time=t_turn,
        arrival_time=tf,
        velocity_out=v_out,
        velocity_in=v_in,
    )

    # Step 9: Validation and residuals
    subluminal_ok = check_subluminal(worldline)
    tau_ok = check_proper_time_consistency(worldline, tau)
    arrival_ok = check_arrival_intersection(worldline, r_ef)

    converged = subluminal_ok and tau_ok and arrival_ok

    # Residual: Euclidean distance between ship final position and Earth at tf
    arrival_residual = float(np.linalg.norm(worldline.positions[-1] - r_ef))
    tau_residual = abs(worldline.proper_times[-1] - tau) / tau if tau > 0 else 0.0
    residual = sqrt(arrival_residual**2 + tau_residual**2)

    # Step 10: Energy
    energy = relativistic_kinetic_energy(beta, mass)

    # Step 11: Arrival relative velocity via relativistic velocity addition
    # Ship velocity in SSBIF at arrival is v_in
    # Earth velocity in SSBIF at arrival
    v_earth_tf = earth_velocity(tf)
    # Velocity of ship relative to Earth = ship velocity transformed to Earth's rest frame
    arrival_rel_vel = relativistic_velocity_addition(v_in, v_earth_tf)

    return TrajectorySolution(
        worldline=worldline,
        velocity_magnitude=beta,
        direction_out=dir_out,
        direction_in=dir_in,
        turnaround_time=t_turn,
        total_proper_time=worldline.proper_times[-1],
        converged=converged,
        residual=residual,
        energy=energy,
        arrival_relative_velocity=arrival_rel_vel,
    )
