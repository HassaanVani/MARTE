"""Tests for ultra-relativistic numerical stability, g-tolerance enforcement,
and jerk-profile rapidity tracking correctness."""

import numpy as np
import pytest

from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR

c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY


# =============================================================================
# Ultra-relativistic numerical stability (relativity.py)
# =============================================================================


class TestUltraRelativisticStability:
    """Verify that relativity functions remain precise at β → 1."""

    def test_lorentz_factor_at_beta_near_one(self):
        """lorentz_factor should not overflow or return inf at β = 1 - 1e-15."""
        from marte.relativity import lorentz_factor

        beta = 1.0 - 1e-15
        gamma = lorentz_factor(beta)
        assert np.isfinite(gamma)
        assert gamma > 1e7  # γ should be huge

    def test_lorentz_factor_vs_rapidity_equivalence(self):
        """lorentz_factor(β) should match cosh(arctanh(β)) at moderate speeds."""
        from marte.relativity import lorentz_factor, lorentz_factor_from_rapidity, rapidity

        for beta in [0.1, 0.5, 0.9, 0.99, 0.999]:
            gamma_beta = lorentz_factor(beta)
            gamma_rap = lorentz_factor_from_rapidity(rapidity(beta))
            assert gamma_beta == pytest.approx(gamma_rap, rel=1e-12)

    def test_lorentz_factor_from_rapidity_large_phi(self):
        """Rapidity-based γ handles extreme rapidity without issues."""
        from marte.relativity import lorentz_factor_from_rapidity

        gamma = lorentz_factor_from_rapidity(10.0)  # β ≈ 0.99999999...
        assert np.isfinite(gamma)
        assert gamma == pytest.approx(np.cosh(10.0), rel=1e-12)

    def test_proper_time_stable_at_high_beta(self):
        """proper_time_elapsed should give finite result at β = 1 - 1e-12."""
        from marte.relativity import proper_time_elapsed

        beta = 1.0 - 1e-12
        dt = 1e7
        tau = proper_time_elapsed(beta, dt)
        assert np.isfinite(tau)
        assert tau > 0
        assert tau < dt

    def test_proper_time_from_rapidity(self):
        """Rapidity-based proper time matches β-based at moderate speeds."""
        from marte.relativity import proper_time_elapsed, proper_time_from_rapidity, rapidity

        dt = 1e7
        for beta in [0.3, 0.6, 0.9, 0.99]:
            tau_beta = proper_time_elapsed(beta, dt)
            tau_rap = proper_time_from_rapidity(rapidity(beta), dt)
            assert tau_beta == pytest.approx(tau_rap, rel=1e-9)

    def test_kinetic_energy_from_rapidity(self):
        """Rapidity-based KE matches β-based at moderate speeds."""
        from marte.relativity import (
            kinetic_energy_from_rapidity,
            rapidity,
            relativistic_kinetic_energy,
        )

        mass = 1000.0
        for beta in [0.1, 0.5, 0.9, 0.99]:
            e_beta = relativistic_kinetic_energy(beta, mass)
            e_rap = kinetic_energy_from_rapidity(rapidity(beta), mass)
            assert e_beta == pytest.approx(e_rap, rel=1e-9)

    def test_kinetic_energy_from_rapidity_large(self):
        """Rapidity-based KE at extreme rapidity gives finite, positive result."""
        from marte.relativity import kinetic_energy_from_rapidity

        energy = kinetic_energy_from_rapidity(20.0, 1000.0)
        assert np.isfinite(energy)
        assert energy > 0

    def test_rapidity_stable_near_one(self):
        """rapidity(β) should return finite values even at β = 1 - 1e-15."""
        from marte.relativity import rapidity

        beta = 1.0 - 1e-15
        phi = rapidity(beta)
        assert np.isfinite(phi)
        assert phi > 10  # Should be a large rapidity

    def test_one_minus_beta_sq_precision(self):
        """(1-β)(1+β) decomposition preserves precision vs naive 1-β²."""
        from marte.relativity import _one_minus_beta_sq

        # At β = 1 - 1e-14, naive 1-β² loses ~14 digits of precision
        beta = 1.0 - 1e-14
        stable = _one_minus_beta_sq(beta)
        # Should be ≈ 2e-14 (from (1-β)(1+β) = 1e-14 * (2 - 1e-14))
        expected = 1e-14 * (2.0 - 1e-14)
        assert stable == pytest.approx(expected, rel=1e-10)

    def test_lorentz_factor_extreme_precision(self):
        """Verify γ at β = 1 - 1e-10 matches analytical expectation."""
        from marte.relativity import lorentz_factor

        eps = 1e-10
        beta = 1.0 - eps
        gamma = lorentz_factor(beta)
        # 1 - β² = (1-β)(1+β) ≈ 2ε for small ε
        # γ = 1/√(2ε) ≈ 70710.678
        expected_gamma = 1.0 / np.sqrt(2 * eps)
        assert gamma == pytest.approx(expected_gamma, rel=1e-5)


# =============================================================================
# G-tolerance enforcement (solver_v2.py)
# =============================================================================


class TestGToleranceEnforcement:
    """Verify that g-tolerance constraints are enforced in the solver."""

    def test_rejects_acceleration_above_peak_g(self):
        """Solver rejects acceleration exceeding peak g-tolerance."""
        from marte.jerk_profiles import GToleranceProfile
        from marte.solver import TrajectoryModel, solve_trajectory

        profile = GToleranceProfile(
            max_sustained_g=3.0,
            max_peak_g=5.0,
            max_peak_duration_s=60.0,
            ramp_time_s=30.0,
        )

        with pytest.raises(ValueError, match="maximum peak"):
            solve_trajectory(
                t0=0.0,
                tf=5 * YEAR,
                proper_time_desired=4.0 * YEAR,
                model=TrajectoryModel.CONSTANT_ACCELERATION,
                proper_acceleration=6.0 * g,  # 6g > 5g peak limit
                g_tolerance=profile,
            )

    def test_rejects_sustained_step_above_limit(self):
        """Step profile at 4g rejected when sustained limit is 3g."""
        from marte.jerk_profiles import GToleranceProfile
        from marte.solver import TrajectoryModel, solve_trajectory

        profile = GToleranceProfile(
            max_sustained_g=3.0,
            max_peak_g=5.0,
            max_peak_duration_s=60.0,
            ramp_time_s=30.0,
        )

        with pytest.raises(ValueError, match="sustained"):
            solve_trajectory(
                t0=0.0,
                tf=5 * YEAR,
                proper_time_desired=4.0 * YEAR,
                model=TrajectoryModel.CONSTANT_ACCELERATION,
                proper_acceleration=4.0 * g,  # 4g > 3g sustained
                acceleration_profile="step",
                g_tolerance=profile,
            )

    def test_accepts_within_limits(self):
        """Solver accepts acceleration within g-tolerance limits."""
        from marte.jerk_profiles import GToleranceProfile
        from marte.solver import TrajectoryModel, solve_trajectory

        profile = GToleranceProfile(
            max_sustained_g=3.0,
            max_peak_g=5.0,
            max_peak_duration_s=60.0,
            ramp_time_s=30.0,
        )

        sol = solve_trajectory(
            t0=0.0,
            tf=5 * YEAR,
            proper_time_desired=4.0 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=2.0 * g,  # 2g < 3g sustained
            g_tolerance=profile,
        )
        assert sol.converged

    def test_no_g_tolerance_allows_any_acceleration(self):
        """Without g_tolerance, any acceleration is accepted (no ValueError raised)."""
        from marte.solver import TrajectoryModel, solve_trajectory

        # 5g without g_tolerance should not raise ValueError
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=5.0 * g,
        )
        # Just verify no ValueError was raised — convergence is a solver concern
        assert sol is not None

    def test_find_all_solutions_respects_g_tolerance(self):
        """find_all_solutions also validates g-tolerance."""
        from marte.jerk_profiles import GToleranceProfile
        from marte.solver_v2 import find_all_solutions

        profile = GToleranceProfile(
            max_sustained_g=1.0,
            max_peak_g=2.0,
            max_peak_duration_s=60.0,
            ramp_time_s=30.0,
        )

        with pytest.raises(ValueError, match="peak"):
            find_all_solutions(
                t0=0.0,
                tf=5 * YEAR,
                proper_time_desired=4.0 * YEAR,
                proper_acceleration=3.0 * g,  # 3g > 2g peak
                g_tolerance=profile,
            )


# =============================================================================
# Jerk-profile rapidity tracking (acceleration.py)
# =============================================================================


class TestJerkProfileRapidityTracking:
    """Verify that jerk-limited phases chain correctly with proper rapidity."""

    def test_step_profile_rapidity_tracking_unchanged(self):
        """Step profile still works identically (regression test)."""
        from marte.acceleration import build_brachistochrone_worldline
        from marte.validation import check_subluminal

        wl = build_brachistochrone_worldline(
            proper_accel=g,
            tau_accel_out=0.5 * YEAR,
            tau_decel_out=0.5 * YEAR,
            tau_accel_in=0.5 * YEAR,
            tau_decel_in=0.5 * YEAR,
            direction_out=np.array([1.0, 0.0, 0.0]),
            direction_in=np.array([-1.0, 0.0, 0.0]),
            start_position=np.zeros(3),
            start_coord_time=0.0,
            n_points_per_phase=50,
            acceleration_profile="step",
        )
        assert check_subluminal(wl)
        assert np.all(np.diff(wl.coord_times) > 0)

    def test_linear_ramp_rapidity_tracking(self):
        """Linear ramp profile produces valid subluminal worldline across phases."""
        from marte.acceleration import build_brachistochrone_worldline
        from marte.validation import check_subluminal

        wl = build_brachistochrone_worldline(
            proper_accel=g,
            tau_accel_out=0.5 * YEAR,
            tau_decel_out=0.5 * YEAR,
            tau_accel_in=0.5 * YEAR,
            tau_decel_in=0.5 * YEAR,
            direction_out=np.array([1.0, 0.0, 0.0]),
            direction_in=np.array([-1.0, 0.0, 0.0]),
            start_position=np.zeros(3),
            start_coord_time=0.0,
            n_points_per_phase=50,
            acceleration_profile="linear_ramp",
            ramp_fraction=0.2,
        )
        assert check_subluminal(wl)
        assert np.all(np.diff(wl.coord_times) > 0)
        assert np.all(np.diff(wl.proper_times) >= 0)

    def test_s_curve_rapidity_tracking(self):
        """S-curve profile produces valid subluminal worldline across phases."""
        from marte.acceleration import build_brachistochrone_worldline
        from marte.validation import check_subluminal

        wl = build_brachistochrone_worldline(
            proper_accel=g,
            tau_accel_out=0.5 * YEAR,
            tau_decel_out=0.5 * YEAR,
            tau_accel_in=0.5 * YEAR,
            tau_decel_in=0.5 * YEAR,
            direction_out=np.array([1.0, 0.0, 0.0]),
            direction_in=np.array([-1.0, 0.0, 0.0]),
            start_position=np.zeros(3),
            start_coord_time=0.0,
            n_points_per_phase=50,
            acceleration_profile="s_curve",
            ramp_fraction=0.2,
        )
        assert check_subluminal(wl)
        assert np.all(np.diff(wl.coord_times) > 0)
        assert np.all(np.diff(wl.proper_times) >= 0)

    def test_jerk_profile_rapidity_less_than_step(self):
        """Jerk-limited profile produces less total rapidity than step profile.

        Because ramp up/down reduce the effective thrust time, the peak speed
        (and total rapidity) should be lower for the same phase duration.
        """
        from marte.acceleration import build_brachistochrone_worldline

        common = dict(
            proper_accel=g,
            tau_accel_out=0.5 * YEAR,
            tau_decel_out=0.5 * YEAR,
            tau_accel_in=0.5 * YEAR,
            tau_decel_in=0.5 * YEAR,
            direction_out=np.array([1.0, 0.0, 0.0]),
            direction_in=np.array([-1.0, 0.0, 0.0]),
            start_position=np.zeros(3),
            start_coord_time=0.0,
            n_points_per_phase=100,
        )

        wl_step = build_brachistochrone_worldline(**common, acceleration_profile="step")
        wl_ramp = build_brachistochrone_worldline(
            **common, acceleration_profile="linear_ramp", ramp_fraction=0.3
        )

        # Compute peak beta from each worldline
        def peak_beta(wl):
            max_beta = 0.0
            for i in range(len(wl.coord_times) - 1):
                dt = wl.coord_times[i + 1] - wl.coord_times[i]
                dr = np.linalg.norm(wl.positions[i + 1] - wl.positions[i])
                max_beta = max(max_beta, dr / (c * dt))
            return max_beta

        # Jerk-limited should reach lower peak speed
        assert peak_beta(wl_ramp) < peak_beta(wl_step)

    def test_jerk_profile_final_rapidity_returned(self):
        """build_jerk_limited_phase returns correct final rapidity."""
        from marte.jerk_profiles import AccelerationProfile, build_jerk_limited_phase

        _, _, _, betas, final_rapidity = build_jerk_limited_phase(
            peak_accel=g,
            tau_phase=0.5 * YEAR,
            profile=AccelerationProfile.LINEAR_RAMP,
            ramp_time=0.1 * YEAR,
            n_points=100,
            direction=np.array([1.0, 0.0, 0.0]),
            start_position=np.zeros(3),
            start_coord_time=0.0,
            start_proper_time=0.0,
            start_rapidity=0.0,
        )

        # Final rapidity should match arctanh of final beta
        expected_rapidity = np.arctanh(betas[-1])
        assert final_rapidity == pytest.approx(expected_rapidity, rel=1e-6)

        # For linear ramp, rapidity should be LESS than step profile value
        step_rapidity = g * 0.5 * YEAR / c
        assert abs(final_rapidity) < step_rapidity

    def test_solver_v2_with_jerk_profile_converges(self):
        """v2 solver converges when using jerk-limited profiles."""
        from marte.solver import TrajectoryModel, solve_trajectory

        sol = solve_trajectory(
            t0=0.0,
            tf=5 * YEAR,
            proper_time_desired=4.0 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=g,
            acceleration_profile="s_curve",
            ramp_fraction=0.15,
        )
        assert sol.converged
