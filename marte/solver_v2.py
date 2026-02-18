"""Numerical solver for constant proper acceleration trajectories (v2).

Finds phase durations and directions for a 4-phase brachistochrone trajectory
that satisfies boundary constraints: depart from Earth at t0, arrive at Earth
at tf, with a desired total proper time.
"""

from math import atan2, sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import root

from marte.acceleration import build_brachistochrone_worldline
from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.orbital import earth_position, earth_velocity
from marte.relativity import (
    relativistic_kinetic_energy,
    relativistic_velocity_addition,
)
from marte.solver import TrajectoryModel, TrajectorySolution
from marte.validation import (
    check_arrival_intersection,
    check_proper_time_consistency,
    check_subluminal,
)

c = SPEED_OF_LIGHT


def find_all_solutions(
    t0: float,
    tf: float,
    proper_time_desired: float,
    mass: float = 1000.0,
    proper_acceleration: float | None = None,
    n_starts: int = 8,
) -> list[TrajectorySolution]:
    """Find all valid trajectory branches by multi-start optimization.

    Launches the solver from n_starts different initial direction angles,
    collects distinct converged solutions.

    Args:
        t0: Departure coordinate time (s).
        tf: Arrival coordinate time (s).
        proper_time_desired: Desired total proper time (s).
        mass: Ship rest mass (kg).
        proper_acceleration: Proper acceleration (m/s²). Defaults to 1g.
        n_starts: Number of starting angles to try.

    Returns:
        List of distinct converged TrajectorySolutions.
    """
    if proper_acceleration is None:
        proper_acceleration = STANDARD_GRAVITY

    a = proper_acceleration
    delta_t = tf - t0
    tau = proper_time_desired

    if delta_t <= 0 or tau <= 0 or tau >= delta_t:
        return []

    r_e0 = earth_position(t0)
    r_ef = earth_position(tf)
    d = r_ef - r_e0
    d_mag = float(np.linalg.norm(d))
    base_theta = np.arctan2(float(d[1]), float(d[0])) if d_mag > 1e-6 else 0.0

    tau_quarter = tau / 4.0
    solutions = []

    # Generate diverse initial guesses: vary both angle and tau fraction
    tau_fractions = [1.0, 0.5, 1.5, 0.25, 2.0]
    guesses = []
    for i in range(n_starts):
        theta = base_theta + 2 * np.pi * i / n_starts
        for frac in tau_fractions:
            guesses.append((tau_quarter * frac, theta))

    for tau_guess, theta in guesses:
        x0 = np.array([tau_guess, tau_guess, theta])

        result = root(
            _residual_symmetric,
            x0,
            args=(t0, tf, tau, a, r_e0, r_ef),
            method="hybr",
            tol=1e-12,
            options={"maxfev": 5000},
        )

        if not result.success:
            continue

        tau_out_half = abs(result.x[0])
        tau_in_half = abs(result.x[1])
        theta_out = result.x[2]

        # Skip if phase durations are unreasonable
        if tau_out_half < 1.0 or tau_in_half < 1.0:
            continue

        # Check for duplicate using direction vector dot product
        dir_candidate = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])
        is_duplicate = False
        for existing in solutions:
            dot = abs(np.dot(dir_candidate, existing.direction_out))
            if dot > 0.995:  # ~5.7° tolerance
                is_duplicate = True
                break

        if is_duplicate:
            continue

        # Build full solution
        dir_out = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])
        dir_in = -dir_out

        n_per_phase = 50
        worldline = build_brachistochrone_worldline(
            proper_accel=a,
            tau_accel_out=tau_out_half,
            tau_decel_out=tau_out_half,
            tau_accel_in=tau_in_half,
            tau_decel_in=tau_in_half,
            direction_out=dir_out,
            direction_in=dir_in,
            start_position=r_e0,
            start_coord_time=t0,
            n_points_per_phase=n_per_phase,
        )

        subluminal_ok = check_subluminal(worldline)
        tau_ok = check_proper_time_consistency(worldline, tau, rtol=1e-3)

        if not (subluminal_ok and tau_ok):
            continue

        peak_rapidity = max(a * tau_out_half / c, a * tau_in_half / c)
        peak_beta = float(np.tanh(peak_rapidity))
        peak_gamma = float(np.cosh(peak_rapidity))

        n = n_per_phase
        phase_boundary_indices = [0, n - 1, 2 * (n - 1), 3 * (n - 1), 4 * (n - 1)]
        phase_boundaries = [float(worldline.coord_times[i]) for i in phase_boundary_indices]
        turnaround_time = float(worldline.coord_times[2 * (n - 1)])

        beta_profile = []
        for j in range(len(worldline.coord_times) - 1):
            dt_seg = worldline.coord_times[j + 1] - worldline.coord_times[j]
            dr = np.linalg.norm(worldline.positions[j + 1] - worldline.positions[j])
            beta_profile.append(float(dr / (c * dt_seg)) if dt_seg > 0 else 0.0)
        beta_profile.append(beta_profile[-1] if beta_profile else 0.0)

        arrival_residual = float(np.linalg.norm(worldline.positions[-1] - r_ef))
        tau_residual = abs(worldline.proper_times[-1] - tau) / tau if tau > 0 else 0.0
        residual = sqrt(arrival_residual**2 + (tau_residual * c) ** 2)

        energy = relativistic_kinetic_energy(peak_beta, mass)

        if len(worldline.positions) >= 2:
            dt_final = worldline.coord_times[-1] - worldline.coord_times[-2]
            v_ship_final = (
                (worldline.positions[-1] - worldline.positions[-2]) / dt_final
                if dt_final > 0
                else np.zeros(3)
            )
        else:
            v_ship_final = np.zeros(3)

        v_earth_tf = earth_velocity(tf)
        arrival_rel_vel = relativistic_velocity_addition(v_ship_final, v_earth_tf)

        sol = TrajectorySolution(
            worldline=worldline,
            velocity_magnitude=peak_beta,
            direction_out=dir_out,
            direction_in=dir_in,
            turnaround_time=turnaround_time,
            total_proper_time=float(worldline.proper_times[-1]),
            converged=True,
            residual=residual,
            energy=energy,
            arrival_relative_velocity=arrival_rel_vel,
            trajectory_model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=a,
            peak_beta=peak_beta,
            peak_gamma=peak_gamma,
            phase_boundaries=phase_boundaries,
            beta_profile=beta_profile,
        )
        solutions.append(sol)

    return solutions


def _symmetric_brachistochrone_estimate(
    distance: float,
    proper_accel: float,
) -> float:
    """Estimate proper time for a symmetric brachistochrone (one-way).

    For a one-way trip of distance d at acceleration a, the proper time
    for each half is τ_half where:
        d/2 = (c²/a)(cosh(aτ_half/c) − 1)

    This inverts to: τ_half = (c/a) acosh(1 + ad/(2c²))

    Returns total one-way proper time = 2 * τ_half.
    """
    arg = 1.0 + proper_accel * distance / (2.0 * c**2)
    if arg < 1.0:
        arg = 1.0
    tau_half = (c / proper_accel) * np.arccosh(arg)
    return 2.0 * tau_half


def _residual(
    params: NDArray[np.float64],
    t0: float,
    tf: float,
    proper_time_desired: float,
    proper_accel: float,
    r_e0: NDArray[np.float64],
    r_ef: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Residual function for the root-finder.

    Unknowns (5): [tau_accel_out, tau_decel_out, tau_accel_in, tau_decel_in, theta_out]

    Constraints (5):
        1-3: Ship final position matches Earth position at tf (3D)
        4:   Total proper time matches desired value
        5:   Total coordinate time matches tf - t0

    Args:
        params: Array of unknowns [tau_ao, tau_do, tau_ai, tau_di, theta_out].
        t0, tf: Departure/arrival coordinate times (s).
        proper_time_desired: Desired total proper time (s).
        proper_accel: Proper acceleration magnitude (m/s²).
        r_e0: Earth position at departure (m), shape (3,).
        r_ef: Earth position at arrival (m), shape (3,).

    Returns:
        Residual vector of shape (5,).
    """
    tau_ao, tau_do, tau_ai, tau_di, theta_out = params

    # Enforce positive phase durations
    tau_ao = abs(tau_ao)
    tau_do = abs(tau_do)
    tau_ai = abs(tau_ai)
    tau_di = abs(tau_di)

    # Outbound direction from angle
    dir_out = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])

    # Build trial worldline
    wl = build_brachistochrone_worldline(
        proper_accel=proper_accel,
        tau_accel_out=tau_ao,
        tau_decel_out=tau_do,
        tau_accel_in=tau_ai,
        tau_decel_in=tau_di,
        direction_out=dir_out,
        direction_in=-dir_out,  # Initial guess: return along same line
        start_position=r_e0,
        start_coord_time=t0,
        n_points_per_phase=5,  # Coarse for speed during root-finding
    )

    # Residuals
    pos_error = wl.positions[-1] - r_ef  # 3D position error (m)
    tau_error = wl.proper_times[-1] - proper_time_desired  # proper time error (s)
    t_error = wl.coord_times[-1] - tf  # coordinate time error (s)

    # Normalize to avoid scale issues
    return np.array([
        pos_error[0] / c,
        pos_error[1] / c,
        pos_error[2] / c,
        tau_error / YEAR,
        t_error / YEAR,
    ])


def _residual_symmetric(
    params: NDArray[np.float64],
    t0: float,
    tf: float,
    proper_time_desired: float,
    proper_accel: float,
    r_e0: NDArray[np.float64],
    r_ef: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Residual for symmetric brachistochrone with free direction.

    For the symmetric case, tau_accel = tau_decel for each leg, reducing to
    3 unknowns: [tau_out_half, tau_in_half, theta_out].

    Constraints (3):
        1: Ship arrives at Earth (distance error)
        2: Total proper time matches
        3: Total coordinate time matches tf - t0
    """
    tau_out_half, tau_in_half, theta_out = params

    tau_out_half = abs(tau_out_half)
    tau_in_half = abs(tau_in_half)

    dir_out = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])

    # Compute turnaround position analytically
    # After accel phase: rapidity = a * tau_out_half / c
    # After decel phase: rapidity = 0 (symmetric)
    # Position after outbound: displacement = (c²/a)[cosh(aτ/c) - 1] for accel
    # plus decel contribution

    # Use full worldline builder with few points
    wl = build_brachistochrone_worldline(
        proper_accel=proper_accel,
        tau_accel_out=tau_out_half,
        tau_decel_out=tau_out_half,
        tau_accel_in=tau_in_half,
        tau_decel_in=tau_in_half,
        direction_out=dir_out,
        direction_in=-dir_out,
        start_position=r_e0,
        start_coord_time=t0,
        n_points_per_phase=3,
    )

    pos_error = wl.positions[-1] - r_ef
    pos_err_mag = float(np.linalg.norm(pos_error))
    tau_error = wl.proper_times[-1] - proper_time_desired
    t_error = wl.coord_times[-1] - tf

    return np.array([
        pos_err_mag / c,
        tau_error / YEAR,
        t_error / YEAR,
    ])


def _solve_v2(
    t0: float,
    tf: float,
    proper_time_desired: float,
    mass: float,
    proper_acceleration: float | None,
) -> TrajectorySolution:
    """Solve for a constant proper acceleration trajectory.

    Uses SciPy root-finding to determine phase durations and direction
    that satisfy the boundary constraints.
    """
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

    if proper_acceleration is None:
        proper_acceleration = STANDARD_GRAVITY  # Default: 1g

    a = proper_acceleration

    # Earth positions
    r_e0 = earth_position(t0)
    r_ef = earth_position(tf)

    # Initial guess from symmetric brachistochrone
    d = r_ef - r_e0
    d_mag = float(np.linalg.norm(d))

    # Direction toward midpoint displacement
    if d_mag > 1e-6:
        theta_guess = atan2(float(d[1]), float(d[0]))
    else:
        theta_guess = 0.0

    # Estimate: distribute proper time equally across 4 phases
    tau_quarter_guess = tau / 4.0

    # Use symmetric solver (3 unknowns) for robustness
    x0 = np.array([tau_quarter_guess, tau_quarter_guess, theta_guess])

    result = root(
        _residual_symmetric,
        x0,
        args=(t0, tf, tau, a, r_e0, r_ef),
        method="hybr",
        tol=1e-12,
        options={"maxfev": 5000},
    )

    if not result.success:
        # Try with different initial guesses
        for factor in [0.5, 1.5, 0.25, 2.0, 0.1]:
            x0_alt = np.array([
                tau_quarter_guess * factor,
                tau_quarter_guess * factor,
                theta_guess + np.pi * (factor - 1),
            ])
            result = root(
                _residual_symmetric,
                x0_alt,
                args=(t0, tf, tau, a, r_e0, r_ef),
                method="hybr",
                tol=1e-12,
                options={"maxfev": 5000},
            )
            if result.success:
                break

    tau_out_half = abs(result.x[0])
    tau_in_half = abs(result.x[1])
    theta_out = result.x[2]

    dir_out = np.array([np.cos(theta_out), np.sin(theta_out), 0.0])
    dir_in = -dir_out

    # Build the final high-resolution worldline
    n_per_phase = 50
    worldline = build_brachistochrone_worldline(
        proper_accel=a,
        tau_accel_out=tau_out_half,
        tau_decel_out=tau_out_half,
        tau_accel_in=tau_in_half,
        tau_decel_in=tau_in_half,
        direction_out=dir_out,
        direction_in=dir_in,
        start_position=r_e0,
        start_coord_time=t0,
        n_points_per_phase=n_per_phase,
    )

    # Compute peak beta (at end of each acceleration phase)
    peak_rapidity_out = a * tau_out_half / c
    peak_rapidity_in = a * tau_in_half / c
    peak_rapidity = max(peak_rapidity_out, peak_rapidity_in)
    peak_beta = float(np.tanh(peak_rapidity))
    peak_gamma = float(np.cosh(peak_rapidity))

    # Phase boundaries in coordinate time
    # Phase 1 ends at index n_per_phase - 1
    # Phase 2 ends at 2*(n_per_phase-1)
    # Phase 3 ends at 3*(n_per_phase-1)
    # Phase 4 ends at 4*(n_per_phase-1)
    n = n_per_phase
    phase_boundary_indices = [0, n - 1, 2 * (n - 1), 3 * (n - 1), 4 * (n - 1)]
    phase_boundaries = [float(worldline.coord_times[i]) for i in phase_boundary_indices]

    # Turnaround is at the end of phase 2 (outbound deceleration complete)
    turnaround_idx = 2 * (n - 1)
    turnaround_time = float(worldline.coord_times[turnaround_idx])

    # Compute beta profile
    beta_profile = []
    for i in range(len(worldline.coord_times) - 1):
        dt = worldline.coord_times[i + 1] - worldline.coord_times[i]
        dr = np.linalg.norm(worldline.positions[i + 1] - worldline.positions[i])
        beta_profile.append(float(dr / (c * dt)) if dt > 0 else 0.0)
    beta_profile.append(beta_profile[-1] if beta_profile else 0.0)

    # Validation
    subluminal_ok = check_subluminal(worldline)
    tau_ok = check_proper_time_consistency(worldline, tau, rtol=1e-4)
    check_arrival_intersection(worldline, r_ef, atol=1e6)

    converged = result.success and subluminal_ok and tau_ok

    # Residual
    arrival_residual = float(np.linalg.norm(worldline.positions[-1] - r_ef))
    tau_residual = abs(worldline.proper_times[-1] - tau) / tau if tau > 0 else 0.0
    residual = sqrt(arrival_residual**2 + (tau_residual * c) ** 2)

    # Energy (peak kinetic energy)
    energy = relativistic_kinetic_energy(peak_beta, mass)

    # Arrival relative velocity
    # At arrival, ship has approximately zero velocity in SSBIF (decelerated to stop)
    # But compute from worldline for accuracy
    if len(worldline.positions) >= 2:
        dt_final = worldline.coord_times[-1] - worldline.coord_times[-2]
        if dt_final > 0:
            v_ship_final = (worldline.positions[-1] - worldline.positions[-2]) / dt_final
        else:
            v_ship_final = np.zeros(3)
    else:
        v_ship_final = np.zeros(3)

    v_earth_tf = earth_velocity(tf)
    arrival_rel_vel = relativistic_velocity_addition(v_ship_final, v_earth_tf)

    return TrajectorySolution(
        worldline=worldline,
        velocity_magnitude=peak_beta,
        direction_out=dir_out,
        direction_in=dir_in,
        turnaround_time=turnaround_time,
        total_proper_time=float(worldline.proper_times[-1]),
        converged=converged,
        residual=residual,
        energy=energy,
        arrival_relative_velocity=arrival_rel_vel,
        trajectory_model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=a,
        peak_beta=peak_beta,
        peak_gamma=peak_gamma,
        phase_boundaries=phase_boundaries,
        beta_profile=beta_profile,
    )
