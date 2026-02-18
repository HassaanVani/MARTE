"""Tests for multi-solution branch detection."""

import numpy as np
import pytest

from marte.constants import STANDARD_GRAVITY, YEAR
from marte.solver_v2 import find_all_solutions
from marte.validation import check_subluminal

g = STANDARD_GRAVITY


def test_short_trip_has_solution():
    """Short trip finds at least one solution."""
    solutions = find_all_solutions(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        proper_acceleration=g,
        n_starts=8,
    )
    assert len(solutions) >= 1


def test_all_solutions_converged():
    """All returned solutions are converged."""
    solutions = find_all_solutions(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        proper_acceleration=g,
        n_starts=8,
    )
    for sol in solutions:
        assert sol.converged


def test_all_solutions_subluminal():
    """All returned solutions are subluminal."""
    solutions = find_all_solutions(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        proper_acceleration=g,
        n_starts=8,
    )
    for sol in solutions:
        assert check_subluminal(sol.worldline)


def test_all_solutions_proper_time_match():
    """All returned solutions match the desired proper time."""
    desired_tau = 4.0 * YEAR
    solutions = find_all_solutions(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=desired_tau,
        proper_acceleration=g,
        n_starts=8,
    )
    for sol in solutions:
        assert sol.total_proper_time == pytest.approx(desired_tau, rel=1e-3)


def test_distinct_solutions_have_different_directions():
    """If multiple solutions found, they have distinct outbound directions."""
    solutions = find_all_solutions(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        proper_acceleration=g,
        n_starts=16,
    )
    if len(solutions) >= 2:
        dirs = [sol.direction_out for sol in solutions]
        for i in range(len(dirs)):
            for j in range(i + 1, len(dirs)):
                # Should not be the same direction
                dot = abs(np.dot(dirs[i], dirs[j]))
                assert dot < 0.999, f"Solutions {i} and {j} are too similar"


def test_long_trip_may_have_multiple_branches():
    """Longer trip with more orbital revolutions may find multiple branches."""
    solutions = find_all_solutions(
        t0=0.0,
        tf=12 * YEAR,
        proper_time_desired=7.0 * YEAR,
        proper_acceleration=g,
        n_starts=16,
    )
    # We expect at least 1, but potentially 2+ for long trips
    assert len(solutions) >= 1
    # All must be valid
    for sol in solutions:
        assert sol.converged
        assert check_subluminal(sol.worldline)


def test_invalid_params_return_empty():
    """Invalid parameters return empty list."""
    # tau >= delta_t
    solutions = find_all_solutions(
        t0=0.0,
        tf=2 * YEAR,
        proper_time_desired=3 * YEAR,
    )
    assert len(solutions) == 0
