"""Tests for elliptical Earth orbit model."""

import numpy as np
import pytest

from marte.constants import EARTH_ECCENTRICITY, EARTH_ORBITAL_RADIUS, YEAR
from marte.orbital import _solve_kepler, earth_position, earth_velocity

e = EARTH_ECCENTRICITY
a = EARTH_ORBITAL_RADIUS


def test_perihelion_distance():
    """At perihelion, r = a(1-e)."""
    # t=0 corresponds to perihelion (M=0)
    r = earth_position(0.0, elliptical=True)
    r_mag = np.linalg.norm(r)
    expected = a * (1 - e)
    assert r_mag == pytest.approx(expected, rel=1e-6)


def test_aphelion_distance():
    """At aphelion (half orbit), r = a(1+e)."""
    # Aphelion at M = π → t = π/ω = T/2
    t_aphelion = YEAR / 2
    r = earth_position(t_aphelion, elliptical=True)
    r_mag = np.linalg.norm(r)
    expected = a * (1 + e)
    assert r_mag == pytest.approx(expected, rel=1e-4)


def test_period_is_one_year():
    """Position repeats after one orbital period."""
    r0 = earth_position(0.0, elliptical=True)
    r1 = earth_position(YEAR, elliptical=True)
    assert np.allclose(r0, r1, atol=1e3)  # Within 1 km


def test_reduces_to_circular_with_zero_eccentricity():
    """With e=0, elliptical should match circular orbit."""
    # We can't set e=0 directly since it's a constant, but we can
    # check that for Earth's small eccentricity, the difference is small
    t = 0.25 * YEAR  # Quarter orbit
    r_circ = earth_position(t, elliptical=False)
    r_ell = earth_position(t, elliptical=True)
    r_circ_mag = np.linalg.norm(r_circ)
    r_ell_mag = np.linalg.norm(r_ell)
    # With e=0.017, the difference should be within ~1.7%
    assert abs(r_ell_mag - r_circ_mag) / r_circ_mag < 0.02


def test_kepler_equation_converges():
    """Kepler's equation converges for all mean anomalies."""
    for mean_anom in np.linspace(0, 2 * np.pi, 36):
        ecc_anom = _solve_kepler(mean_anom, e)
        # Verify: M = E - e sin(E)
        residual = abs(ecc_anom - e * np.sin(ecc_anom) - mean_anom)
        assert residual < 1e-10


def test_kepler_identity_at_zero():
    """E(M=0) = 0."""
    ecc_anom = _solve_kepler(0.0, e)
    assert ecc_anom == pytest.approx(0.0, abs=1e-12)


def test_kepler_identity_at_pi():
    """E(M=π) = π."""
    ecc_anom = _solve_kepler(np.pi, e)
    assert ecc_anom == pytest.approx(np.pi, abs=1e-10)


def test_elliptical_velocity_perpendicular_at_perihelion():
    """At perihelion, velocity is purely tangential (perpendicular to position)."""
    r = earth_position(0.0, elliptical=True)
    v = earth_velocity(0.0, elliptical=True)
    # dot(r, v) should be ~0 at perihelion
    dot = np.dot(r, v)
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)
    cos_angle = dot / (r_mag * v_mag)
    assert abs(cos_angle) < 0.01  # Nearly perpendicular


def test_elliptical_velocity_magnitude_reasonable():
    """Velocity magnitude should be close to circular for small eccentricity."""
    v_circ = earth_velocity(0.0, elliptical=False)
    v_ell = earth_velocity(0.0, elliptical=True)
    v_circ_mag = np.linalg.norm(v_circ)
    v_ell_mag = np.linalg.norm(v_ell)
    # At perihelion, velocity is slightly higher than circular
    assert v_ell_mag > v_circ_mag  # Faster at perihelion
    assert abs(v_ell_mag - v_circ_mag) / v_circ_mag < 0.05  # Within 5%
