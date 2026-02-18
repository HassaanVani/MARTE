"""Tests for marte.solver — analytical trajectory solver."""

import numpy as np
import pytest

from marte.constants import SPEED_OF_LIGHT, YEAR


def test_solver_converges_basic():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.converged


def test_solver_proper_time_matches():
    from marte.solver import solve_trajectory

    desired_tau = 1.5 * YEAR
    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=desired_tau)
    assert sol.total_proper_time == pytest.approx(desired_tau, rel=1e-6)


def test_solver_subluminal():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.velocity_magnitude < 1.0


def test_solver_residual_small():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.residual < 1e-6


# --- Additional solver tests ---


def test_solver_has_energy_field():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.energy > 0


def test_solver_has_arrival_relative_velocity():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.arrival_relative_velocity.shape == (3,)
    arrival_speed = np.linalg.norm(sol.arrival_relative_velocity)
    assert arrival_speed < SPEED_OF_LIGHT


def test_solver_high_gamma():
    """Test with high time dilation (γ ≈ 2)."""
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.0 * YEAR)
    assert sol.converged
    assert sol.velocity_magnitude == pytest.approx(0.866, rel=1e-2)


def test_solver_rejects_tau_geq_delta_t():
    """Proper time must be less than coordinate time for relativistic trajectories."""
    from marte.solver import solve_trajectory

    with pytest.raises(ValueError):
        solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=2.0 * YEAR)


def test_solver_rejects_negative_proper_time():
    from marte.solver import solve_trajectory

    with pytest.raises(ValueError):
        solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=-1.0 * YEAR)


def test_solver_rejects_reversed_times():
    from marte.solver import solve_trajectory

    with pytest.raises(ValueError):
        solve_trajectory(t0=2 * YEAR, tf=0.0, proper_time_desired=1.0 * YEAR)
