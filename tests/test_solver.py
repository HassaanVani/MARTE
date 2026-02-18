"""Tests for marte.solver — constrained trajectory root-finding."""

import pytest

from marte.constants import YEAR


@pytest.mark.skip(reason="not yet implemented")
def test_solver_converges_basic():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.converged


@pytest.mark.skip(reason="not yet implemented")
def test_solver_proper_time_matches():
    from marte.solver import solve_trajectory

    desired_tau = 1.5 * YEAR
    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=desired_tau)
    assert sol.total_proper_time == pytest.approx(desired_tau, rel=1e-6)


@pytest.mark.skip(reason="not yet implemented")
def test_solver_subluminal():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.velocity_magnitude < 1.0


@pytest.mark.skip(reason="not yet implemented")
def test_solver_residual_small():
    from marte.solver import solve_trajectory

    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.residual < 1e-6
