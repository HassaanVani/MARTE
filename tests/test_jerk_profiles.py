"""Tests for marte.jerk_profiles — jerk-limited acceleration profiles."""

import numpy as np
import pytest

from marte.acceleration import build_acceleration_phase
from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.jerk_profiles import (
    AccelerationProfile,
    acceleration_schedule,
    build_jerk_limited_phase,
)

c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY


# --- acceleration_schedule tests ---


def test_step_profile_constant():
    """STEP profile gives constant acceleration."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.STEP,
        ramp_time=0.1 * YEAR,
        n_points=100,
    )
    assert np.allclose(a_pts, g)


def test_linear_ramp_starts_at_zero():
    """LINEAR_RAMP starts at a=0."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.LINEAR_RAMP,
        ramp_time=0.2 * YEAR,
        n_points=100,
    )
    assert a_pts[0] == pytest.approx(0.0)


def test_linear_ramp_ends_at_zero():
    """LINEAR_RAMP ends at a=0."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.LINEAR_RAMP,
        ramp_time=0.2 * YEAR,
        n_points=100,
    )
    assert a_pts[-1] == pytest.approx(0.0, abs=g * 0.02)


def test_linear_ramp_reaches_peak():
    """LINEAR_RAMP reaches peak_accel in the middle."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.LINEAR_RAMP,
        ramp_time=0.2 * YEAR,
        n_points=100,
    )
    assert np.max(a_pts) == pytest.approx(g, rel=0.01)


def test_linear_ramp_no_discontinuities():
    """LINEAR_RAMP has no discontinuities in a(τ)."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.LINEAR_RAMP,
        ramp_time=0.2 * YEAR,
        n_points=1000,
    )
    da = np.diff(a_pts)
    dt = np.diff(tau_pts)
    jerk = da / dt
    # No sudden jumps: max jerk should be bounded
    max_jerk = np.max(np.abs(jerk))
    # Jerk should be bounded by peak_accel / ramp_time (+ small numerical margin)
    expected_max_jerk = g / (0.2 * YEAR) * 1.5
    assert max_jerk < expected_max_jerk


def test_s_curve_starts_at_zero():
    """S_CURVE starts at a=0."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.S_CURVE,
        ramp_time=0.2 * YEAR,
        n_points=100,
    )
    assert a_pts[0] == pytest.approx(0.0)


def test_s_curve_no_discontinuities_in_acceleration():
    """S_CURVE has no discontinuities in a(τ)."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.S_CURVE,
        ramp_time=0.2 * YEAR,
        n_points=1000,
    )
    da = np.diff(a_pts)
    dt = np.diff(tau_pts)
    jerk = da / dt
    # S-curve jerk should be smoother than linear ramp
    max_jerk = np.max(np.abs(jerk))
    expected_max_jerk = g * np.pi / (0.2 * YEAR) * 1.1  # Theoretical max for half-cosine
    assert max_jerk < expected_max_jerk


def test_s_curve_no_discontinuities_in_jerk():
    """S_CURVE has no discontinuities in da/dτ (jerk is continuous)."""
    tau_pts, a_pts = acceleration_schedule(
        tau_phase=1.0 * YEAR,
        peak_accel=g,
        profile=AccelerationProfile.S_CURVE,
        ramp_time=0.2 * YEAR,
        n_points=2000,
    )
    da = np.diff(a_pts)
    dt = np.diff(tau_pts)
    jerk = da / dt

    # Jerk changes (second derivative of a)
    djerk = np.diff(jerk)
    # The djerk should be smooth — no sudden jumps beyond numerical error
    # At the transition from ramp to constant, jerk goes to 0 smoothly
    max_djerk = np.max(np.abs(djerk))
    # Compare to expected scale: max jerk * dt (numerical derivative noise)
    expected_scale = np.max(np.abs(jerk)) * np.mean(dt) * 50  # generous bound
    assert max_djerk < expected_scale


# --- build_jerk_limited_phase tests ---


def test_step_matches_constant_acceleration():
    """STEP profile matches Phase 3a constant-acceleration result."""
    direction = np.array([1.0, 0.0, 0.0])
    start_pos = np.array([0.0, 0.0, 0.0])
    tau_dur = 0.5 * YEAR
    n = 100

    # Phase 3a reference
    ct_ref, ps_ref, pt_ref, bs_ref = build_acceleration_phase(
        proper_accel=g,
        tau_duration=tau_dur,
        n_points=n,
        direction=direction,
        start_position=start_pos,
        start_coord_time=0.0,
        start_proper_time=0.0,
        start_rapidity=0.0,
    )

    # Jerk-limited STEP
    ct_jl, ps_jl, pt_jl, bs_jl = build_jerk_limited_phase(
        peak_accel=g,
        tau_phase=tau_dur,
        profile=AccelerationProfile.STEP,
        ramp_time=0.0,
        n_points=n,
        direction=direction,
        start_position=start_pos,
        start_coord_time=0.0,
        start_proper_time=0.0,
        start_rapidity=0.0,
    )

    # Should match closely (numerical integration vs analytical)
    assert ct_jl[-1] == pytest.approx(ct_ref[-1], rel=1e-4)
    assert np.allclose(ps_jl[-1], ps_ref[-1], rtol=1e-3)
    assert bs_jl[-1] == pytest.approx(bs_ref[-1], rel=1e-4)


def test_jerk_bounded():
    """Jerk is bounded: |da/dτ| ≤ j_max everywhere."""
    tau_phase = 1.0 * YEAR
    ramp_time = 0.2 * YEAR
    n = 2000

    _, a_pts = acceleration_schedule(
        tau_phase=tau_phase,
        peak_accel=5 * g,  # 5g burst
        profile=AccelerationProfile.S_CURVE,
        ramp_time=ramp_time,
        n_points=n,
    )

    tau_pts = np.linspace(0, tau_phase, n)
    dt = np.diff(tau_pts)
    jerk = np.diff(a_pts) / dt

    # Maximum jerk for S-curve: peak_accel * π / (2 * ramp_time)
    j_max = 5 * g * np.pi / (2 * ramp_time) * 1.1  # 10% margin
    assert np.all(np.abs(jerk) <= j_max)


# --- EXIT CRITERION: 5g-burst Proxima Centauri with smooth transitions ---


def test_5g_burst_with_smooth_transitions():
    """5g burst acceleration with S-curve ramp produces valid phase.

    This is the exit criterion for Phase 3g: demonstrate that a 5g
    burst with smooth jerk-limited transitions produces physically
    valid results (subluminal, monotonic time, bounded jerk).
    """
    direction = np.array([1.0, 0.0, 0.0])
    start_pos = np.array([0.0, 0.0, 0.0])
    tau_dur = 0.5 * YEAR
    ramp_time = 0.05 * YEAR  # ~18 days ramp

    ct, ps, pt, bs = build_jerk_limited_phase(
        peak_accel=5 * g,
        tau_phase=tau_dur,
        profile=AccelerationProfile.S_CURVE,
        ramp_time=ramp_time,
        n_points=200,
        direction=direction,
        start_position=start_pos,
        start_coord_time=0.0,
        start_proper_time=0.0,
        start_rapidity=0.0,
    )

    # Subluminal
    assert np.all(bs < 1.0)

    # Monotonic coordinate time
    assert np.all(np.diff(ct) > 0)

    # Monotonic proper time
    assert np.all(np.diff(pt) >= 0)

    # Beta increases (accelerating phase)
    assert bs[-1] > bs[0]

    # Reaches high speed (5g for 0.5yr should reach ~0.98c)
    assert bs[-1] > 0.9
