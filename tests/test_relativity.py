"""Tests for marte.relativity — Lorentz factor, proper time, energy, momentum, rapidity."""

import numpy as np
import pytest

from marte.constants import SPEED_OF_LIGHT


@pytest.mark.parametrize(
    ("beta", "expected_gamma"),
    [
        (0.0, 1.0),
        (0.6, 1.25),
        (0.866, 2.0),
    ],
)
def test_lorentz_factor_known_values(beta, expected_gamma):
    from marte.relativity import lorentz_factor

    assert lorentz_factor(beta) == pytest.approx(expected_gamma, rel=1e-3)


def test_lorentz_factor_always_geq_one(standard_betas):
    from marte.relativity import lorentz_factor

    for beta in standard_betas:
        assert lorentz_factor(beta) >= 1.0


def test_proper_time_less_than_coord_time():
    from marte.relativity import proper_time_elapsed

    coord_time = 1e7  # ~115 days
    for beta in [0.1, 0.3, 0.6, 0.9]:
        tau = proper_time_elapsed(beta, coord_time)
        assert tau < coord_time


def test_proper_time_zero_velocity():
    from marte.relativity import proper_time_elapsed

    coord_time = 1e7
    assert proper_time_elapsed(0.0, coord_time) == pytest.approx(coord_time)


def test_relativistic_kinetic_energy_at_rest():
    from marte.relativity import relativistic_kinetic_energy

    assert relativistic_kinetic_energy(0.0, 1000.0) == pytest.approx(0.0)


def test_relativistic_kinetic_energy_high_beta():
    from marte.relativity import relativistic_kinetic_energy

    # At β=0.99, γ ≈ 7.089, E_k = (γ-1)mc² ≈ 6.089 * 1000 * c²
    energy = relativistic_kinetic_energy(0.99, 1000.0)
    assert energy > 0


def test_relativistic_momentum_at_rest():
    from marte.relativity import relativistic_momentum

    assert relativistic_momentum(0.0, 1000.0) == pytest.approx(0.0)


def test_rapidity_roundtrip(standard_betas):
    from marte.relativity import beta_from_rapidity, rapidity

    for beta in standard_betas:
        if beta < 1.0:
            phi = rapidity(beta)
            recovered = beta_from_rapidity(phi)
            assert recovered == pytest.approx(beta)


def test_rapidity_zero():
    from marte.relativity import rapidity

    assert rapidity(0.0) == pytest.approx(0.0)


# --- New tests for relativistic_velocity_addition ---


def test_velocity_addition_zero_frame():
    """Adding zero frame velocity returns original velocity."""
    from marte.relativity import relativistic_velocity_addition

    v_obj = np.array([1e8, 0.0, 0.0])
    v_frame = np.array([0.0, 0.0, 0.0])
    result = relativistic_velocity_addition(v_obj, v_frame)
    np.testing.assert_allclose(result, v_obj, atol=1.0)


def test_velocity_addition_collinear():
    """Collinear velocity addition should match 1D formula."""
    from marte.relativity import relativistic_velocity_addition

    c = SPEED_OF_LIGHT
    v = 0.5 * c
    u = 0.5 * c
    # 1D formula: (v - u) / (1 - v*u/c²)
    expected = (v - u) / (1.0 - v * u / c**2)

    v_obj = np.array([v, 0.0, 0.0])
    v_frame = np.array([u, 0.0, 0.0])
    result = relativistic_velocity_addition(v_obj, v_frame)
    assert result[0] == pytest.approx(expected, rel=1e-9)
    assert result[1] == pytest.approx(0.0, abs=1e-6)
    assert result[2] == pytest.approx(0.0, abs=1e-6)


def test_velocity_addition_subluminal():
    """Adding two subluminal velocities should remain subluminal."""
    from marte.relativity import relativistic_velocity_addition

    c = SPEED_OF_LIGHT
    v_obj = np.array([0.9 * c, 0.0, 0.0])
    v_frame = np.array([0.9 * c, 0.0, 0.0])
    result = relativistic_velocity_addition(v_obj, v_frame)
    result_speed = np.linalg.norm(result)
    assert result_speed < c
