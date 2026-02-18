"""Tests for marte.relativity — Lorentz factor, proper time, energy, momentum, rapidity."""

import pytest


@pytest.mark.skip(reason="not yet implemented")
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


@pytest.mark.skip(reason="not yet implemented")
def test_lorentz_factor_always_geq_one(standard_betas):
    from marte.relativity import lorentz_factor

    for beta in standard_betas:
        assert lorentz_factor(beta) >= 1.0


@pytest.mark.skip(reason="not yet implemented")
def test_proper_time_less_than_coord_time():
    from marte.relativity import proper_time_elapsed

    coord_time = 1e7  # ~115 days
    for beta in [0.1, 0.3, 0.6, 0.9]:
        tau = proper_time_elapsed(beta, coord_time)
        assert tau < coord_time


@pytest.mark.skip(reason="not yet implemented")
def test_proper_time_zero_velocity():
    from marte.relativity import proper_time_elapsed

    coord_time = 1e7
    assert proper_time_elapsed(0.0, coord_time) == pytest.approx(coord_time)


@pytest.mark.skip(reason="not yet implemented")
def test_relativistic_kinetic_energy_at_rest():
    from marte.relativity import relativistic_kinetic_energy

    assert relativistic_kinetic_energy(0.0, 1000.0) == pytest.approx(0.0)


@pytest.mark.skip(reason="not yet implemented")
def test_relativistic_kinetic_energy_high_beta():
    from marte.relativity import relativistic_kinetic_energy

    # At β=0.99, γ ≈ 7.089, E_k = (γ-1)mc² ≈ 6.089 * 1000 * c²
    energy = relativistic_kinetic_energy(0.99, 1000.0)
    assert energy > 0


@pytest.mark.skip(reason="not yet implemented")
def test_relativistic_momentum_at_rest():
    from marte.relativity import relativistic_momentum

    assert relativistic_momentum(0.0, 1000.0) == pytest.approx(0.0)


@pytest.mark.skip(reason="not yet implemented")
def test_rapidity_roundtrip(standard_betas):
    from marte.relativity import beta_from_rapidity, rapidity

    for beta in standard_betas:
        if beta < 1.0:
            phi = rapidity(beta)
            recovered = beta_from_rapidity(phi)
            assert recovered == pytest.approx(beta)


@pytest.mark.skip(reason="not yet implemented")
def test_rapidity_zero():
    from marte.relativity import rapidity

    assert rapidity(0.0) == pytest.approx(0.0)
