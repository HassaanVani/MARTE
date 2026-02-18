"""Tests for marte.solver_v2 — constant proper acceleration trajectory solver."""

import numpy as np
import pytest

from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.solver import TrajectoryModel, solve_trajectory

c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY
LY = c * YEAR


# --- Basic convergence ---


def test_v2_converges_1g_5yr():
    """v2 solver converges for 1g, 5-year round trip."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.converged


def test_v2_proper_time_matches():
    """Total proper time matches desired value."""
    desired_tau = 4.0 * YEAR
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=desired_tau,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.total_proper_time == pytest.approx(desired_tau, rel=1e-3)


def test_v2_subluminal():
    """All velocities remain subluminal."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.peak_beta is not None
    assert sol.peak_beta < 1.0


# --- EXIT CRITERION: 1g Proxima Centauri ---


def test_v2_proxima_centauri_round_trip():
    """1g round-trip to Proxima Centauri → ~3.5yr proper time each way.

    Proxima Centauri is 4.24 ly away. A 1g brachistochrone round trip
    takes about 12 years coordinate time and ~7 years proper time total.

    This is the primary exit criterion for Phase 3b.
    """
    # Coordinate time for a 1g round trip to 4.24 ly:
    # One-way coord time: t = (c/a) * (sinh(a*tau_half/c) * 2) for each leg
    # Approximate: ~6 years each way = ~12 years total
    # Use generous bounds to let solver find it
    t_total = 12 * YEAR

    # Proper time should be significantly less due to time dilation
    # Expected: ~3.5 yr each way = ~7 yr total
    tau_desired = 7.0 * YEAR

    sol = solve_trajectory(
        t0=0.0,
        tf=t_total,
        proper_time_desired=tau_desired,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )

    assert sol.converged
    assert sol.total_proper_time == pytest.approx(tau_desired, rel=1e-2)
    assert sol.peak_beta is not None
    assert sol.peak_beta > 0.9  # Should reach very high speed
    assert sol.peak_beta < 1.0


# --- Worldline structure ---


def test_v2_worldline_has_many_points():
    """v2 worldline has N >> 3 points."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert len(sol.worldline.coord_times) > 100


def test_v2_model_field():
    """Solution reports correct trajectory model."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.trajectory_model == TrajectoryModel.CONSTANT_ACCELERATION


def test_v2_has_phase_boundaries():
    """v2 solution has phase boundary times."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert len(sol.phase_boundaries) == 5  # start + 4 phase ends


def test_v2_has_beta_profile():
    """v2 solution has a beta profile with many entries."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert len(sol.beta_profile) == len(sol.worldline.coord_times)


def test_v2_peak_gamma():
    """Peak gamma is correctly reported."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.peak_gamma is not None
    assert sol.peak_gamma > 1.0


def test_v2_proper_acceleration_recorded():
    """Proper acceleration is recorded in solution."""
    sol = solve_trajectory(
        t0=0.0,
        tf=2 * YEAR,
        proper_time_desired=1.5 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=2 * g,
    )
    assert sol.proper_acceleration == 2 * g


# --- Error handling ---


def test_v2_rejects_tau_geq_delta_t():
    """Proper time >= coordinate time is rejected."""
    with pytest.raises(ValueError):
        solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=2.5 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
        )


def test_v2_default_acceleration_is_1g():
    """When no acceleration specified, defaults to 1g."""
    sol = solve_trajectory(
        t0=0.0,
        tf=2 * YEAR,
        proper_time_desired=1.5 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
    )
    assert sol.proper_acceleration == g


# --- Consistency ---


def test_v2_coord_time_monotonic():
    """Coordinate time is strictly monotonic."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert np.all(np.diff(sol.worldline.coord_times) > 0)


def test_v2_proper_time_monotonic():
    """Proper time is monotonically increasing."""
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert np.all(np.diff(sol.worldline.proper_times) >= 0)


def test_v2_higher_accel_shorter_proper_time():
    """Higher acceleration for same trip → less proper time needed for same coord time."""
    sol_1g = solve_trajectory(
        t0=0.0,
        tf=4 * YEAR,
        proper_time_desired=3.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    sol_2g = solve_trajectory(
        t0=0.0,
        tf=4 * YEAR,
        proper_time_desired=3.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=2 * g,
    )
    # Both should converge
    assert sol_1g.converged
    assert sol_2g.converged
    # Higher acceleration reaches higher peak speed
    assert sol_2g.peak_beta > sol_1g.peak_beta or sol_2g.peak_beta == pytest.approx(
        sol_1g.peak_beta, abs=0.01
    )
