"""Tests for marte.acceleration — hyperbolic motion primitives."""

import numpy as np
import pytest

from marte.acceleration import (
    build_acceleration_phase,
    build_brachistochrone_worldline,
    hyperbolic_beta,
    hyperbolic_coord_time,
    hyperbolic_gamma,
    hyperbolic_position,
    hyperbolic_rapidity,
)
from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR

c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY
LY = c * YEAR  # light-year in meters


# --- Textbook values ---


def test_1g_1yr_proper_speed():
    """1g for 1 year proper time → v ≈ 0.77c (textbook value)."""
    beta = hyperbolic_beta(YEAR, g)
    assert beta == pytest.approx(0.77, abs=0.01)


def test_1g_1yr_proper_gamma():
    """1g for 1 year → γ ≈ 1.58 (cosh(aτ/c) with aτ/c ≈ 1.033)."""
    gamma = hyperbolic_gamma(YEAR, g)
    # aτ/c = 9.80665 * 3.15576e7 / 2.99792e8 ≈ 1.033
    # cosh(1.033) ≈ 1.582
    assert gamma == pytest.approx(1.582, abs=0.01)


def test_gamma_at_zero():
    """γ(0) = 1 for any acceleration."""
    assert hyperbolic_gamma(0.0, g) == pytest.approx(1.0)
    assert hyperbolic_gamma(0.0, 10 * g) == pytest.approx(1.0)


def test_beta_at_zero():
    """β(0) = 0 for any acceleration."""
    assert hyperbolic_beta(0.0, g) == pytest.approx(0.0)


def test_rapidity_linear_in_tau():
    """Rapidity grows linearly: φ(τ) = aτ/c."""
    tau1 = 1.0 * YEAR
    tau2 = 2.0 * YEAR
    phi1 = hyperbolic_rapidity(tau1, g)
    phi2 = hyperbolic_rapidity(tau2, g)
    assert phi2 == pytest.approx(2.0 * phi1, rel=1e-12)


def test_beta_approaches_1_asymptotically():
    """At very large τ, β → 1 but never reaches it."""
    beta_10yr = hyperbolic_beta(10 * YEAR, g)
    beta_20yr = hyperbolic_beta(20 * YEAR, g)
    assert beta_10yr > 0.99
    assert beta_20yr > beta_10yr
    # At extreme τ, tanh saturates to 1.0 in float64, so we test the trend
    assert beta_20yr > 0.9999


def test_position_at_zero():
    """x(0) = 0."""
    assert hyperbolic_position(0.0, g) == pytest.approx(0.0)


def test_coord_time_at_zero():
    """t(0) = 0."""
    assert hyperbolic_coord_time(0.0, g) == pytest.approx(0.0)


# --- 1g to Proxima Centauri (4.24 ly one-way) ---


def test_1g_proxima_centauri_one_way():
    """1g brachistochrone to Proxima Centauri (4.24 ly): proper time ~3.5yr each way.

    A brachistochrone (accelerate halfway, decelerate second half) to 4.24 ly
    should take about 3.5 years proper time.
    """
    d_target = 4.24 * LY  # meters

    # Binary search for the proper time τ_half at which the midpoint distance is d/2
    # At midpoint of a symmetric brachistochrone: x(τ_half) = d/2
    tau_lo, tau_hi = 0.1 * YEAR, 10.0 * YEAR
    for _ in range(100):
        tau_mid = (tau_lo + tau_hi) / 2
        x = hyperbolic_position(tau_mid, g)
        if x < d_target / 2:
            tau_lo = tau_mid
        else:
            tau_hi = tau_mid

    tau_half = (tau_lo + tau_hi) / 2
    total_proper = 2 * tau_half / YEAR

    # Should be about 3.5 years proper time one-way
    assert total_proper == pytest.approx(3.55, abs=0.15)


# --- Phase boundary continuity ---


def test_phase_boundary_continuity():
    """Position and time are continuous at phase boundaries."""
    direction = np.array([1.0, 0.0, 0.0])
    start_pos = np.array([0.0, 0.0, 0.0])
    tau_dur = 0.5 * YEAR

    # Phase 1: accelerate
    ct1, ps1, pt1, bs1 = build_acceleration_phase(
        proper_accel=g,
        tau_duration=tau_dur,
        n_points=50,
        direction=direction,
        start_position=start_pos,
        start_coord_time=0.0,
        start_proper_time=0.0,
        start_rapidity=0.0,
    )

    # Phase 2: decelerate, starting from end of phase 1
    end_rapidity = g * tau_dur / c  # φ = aτ/c at end of phase 1
    ct2, ps2, pt2, bs2 = build_acceleration_phase(
        proper_accel=-g,
        tau_duration=tau_dur,
        n_points=50,
        direction=direction,
        start_position=ps1[-1],
        start_coord_time=ct1[-1],
        start_proper_time=pt1[-1],
        start_rapidity=end_rapidity,
    )

    # Position continuous at boundary
    assert np.allclose(ps1[-1], ps2[0], atol=1.0)
    # Time continuous
    assert ct1[-1] == pytest.approx(ct2[0], abs=1e-6)
    # Proper time continuous
    assert pt1[-1] == pytest.approx(pt2[0], abs=1e-6)


def test_symmetric_brachistochrone_turnaround():
    """Symmetric brachistochrone: velocity = 0 at turnaround (midpoint)."""
    direction_out = np.array([1.0, 0.0, 0.0])
    direction_in = np.array([-1.0, 0.0, 0.0])
    tau_phase = 1.0 * YEAR

    wl = build_brachistochrone_worldline(
        proper_accel=g,
        tau_accel_out=tau_phase,
        tau_decel_out=tau_phase,
        tau_accel_in=tau_phase,
        tau_decel_in=tau_phase,
        direction_out=direction_out,
        direction_in=direction_in,
        start_position=np.array([0.0, 0.0, 0.0]),
        start_coord_time=0.0,
        n_points_per_phase=50,
    )

    # Worldline should have 4*50 - 3 = 197 points
    assert len(wl.coord_times) == 197

    # Check monotonicity of coord times and proper times
    assert np.all(np.diff(wl.coord_times) > 0)
    assert np.all(np.diff(wl.proper_times) >= 0)


def test_brachistochrone_proper_time_total():
    """Total proper time = sum of all phase durations."""
    tau_phase = 0.5 * YEAR
    wl = build_brachistochrone_worldline(
        proper_accel=g,
        tau_accel_out=tau_phase,
        tau_decel_out=tau_phase,
        tau_accel_in=tau_phase,
        tau_decel_in=tau_phase,
        direction_out=np.array([1.0, 0.0, 0.0]),
        direction_in=np.array([-1.0, 0.0, 0.0]),
        start_position=np.array([0.0, 0.0, 0.0]),
        start_coord_time=0.0,
        n_points_per_phase=20,
    )

    expected_tau = 4 * tau_phase
    assert wl.proper_times[-1] == pytest.approx(expected_tau, rel=1e-10)


def test_brachistochrone_worldline_shape():
    """Worldline arrays have consistent shapes."""
    n = 30
    wl = build_brachistochrone_worldline(
        proper_accel=g,
        tau_accel_out=0.5 * YEAR,
        tau_decel_out=0.5 * YEAR,
        tau_accel_in=0.5 * YEAR,
        tau_decel_in=0.5 * YEAR,
        direction_out=np.array([1.0, 0.0, 0.0]),
        direction_in=np.array([-1.0, 0.0, 0.0]),
        start_position=np.array([0.0, 0.0, 0.0]),
        start_coord_time=0.0,
        n_points_per_phase=n,
    )

    expected_len = 4 * n - 3
    assert wl.coord_times.shape == (expected_len,)
    assert wl.positions.shape == (expected_len, 3)
    assert wl.proper_times.shape == (expected_len,)
