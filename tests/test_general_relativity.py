"""Tests for general_relativity module — Schwarzschild metric corrections."""

import numpy as np
import pytest

from marte.constants import (
    AU,
    GM_SUN,
    SCHWARZSCHILD_RADIUS_SUN,
    SPEED_OF_LIGHT,
    YEAR,
)
from marte.general_relativity import (
    GRDiagnostics,
    gr_correction,
    gr_corrected_proper_time,
    gr_proper_time_factor,
    gravitational_potential_sun,
    schwarzschild_time_dilation_factor,
    sr_proper_time,
)
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT
R_SUN = 6.957e8  # solar radius in meters


class TestSchwarzschildRadius:
    def test_schwarzschild_radius_value(self):
        """Schwarzschild radius of the Sun ≈ 2953 m."""
        assert SCHWARZSCHILD_RADIUS_SUN == pytest.approx(2953, rel=0.01)

    def test_schwarzschild_radius_formula(self):
        """r_s = 2GM/c² matches the constant."""
        r_s = 2 * GM_SUN / c**2
        assert r_s == pytest.approx(SCHWARZSCHILD_RADIUS_SUN, rel=1e-10)


class TestTimeDilation:
    def test_dilation_at_1au(self):
        """At 1 AU, r_s/r ≈ 1.97e-8."""
        r_s = SCHWARZSCHILD_RADIUS_SUN
        ratio = r_s / AU
        assert ratio == pytest.approx(1.97e-8, rel=0.05)

    def test_dilation_at_solar_surface(self):
        """At solar surface, r_s/r ≈ 4.24e-6."""
        r_s = SCHWARZSCHILD_RADIUS_SUN
        ratio = r_s / R_SUN
        assert ratio == pytest.approx(4.24e-6, rel=0.05)

    def test_factor_at_1au(self):
        """Time dilation factor at 1 AU is very close to 1."""
        factor = schwarzschild_time_dilation_factor(AU)
        assert factor == pytest.approx(1.0, abs=1e-7)
        assert factor < 1.0  # gravity slows clocks

    def test_factor_at_solar_surface(self):
        """Time dilation factor at solar surface is measurably less than 1."""
        factor = schwarzschild_time_dilation_factor(R_SUN)
        assert factor < 1.0
        # 1 - factor ≈ r_s/(2r) ≈ 2.12e-6
        assert 1.0 - factor == pytest.approx(2.12e-6, rel=0.05)


class TestGRProperTimeFactor:
    def test_reduces_to_sr_at_infinity(self):
        """As r → ∞, gr_proper_time_factor → √(1 - β²) (pure SR)."""
        r_large = 1e20  # effectively infinite
        beta = 0.6
        from math import sqrt
        expected = sqrt(1.0 - beta**2)
        result = gr_proper_time_factor(r_large, beta)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_reduces_to_grav_at_rest(self):
        """At β=0, gr_proper_time_factor → √(1 - r_s/r) (pure gravitational)."""
        r = AU
        result = gr_proper_time_factor(r, 0.0)
        expected = schwarzschild_time_dilation_factor(r)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_less_than_sr_in_gravity(self):
        """GR factor < SR factor when in gravity well (extra dilation)."""
        beta = 0.5
        from math import sqrt
        sr_factor = sqrt(1.0 - beta**2)
        gr_factor = gr_proper_time_factor(AU, beta)
        assert gr_factor < sr_factor


class TestGravitationalPotential:
    def test_potential_at_1au(self):
        """Gravitational potential at 1 AU ≈ -8.87e8 J/kg."""
        phi = gravitational_potential_sun(AU)
        assert phi == pytest.approx(-8.87e8, rel=0.01)

    def test_potential_negative(self):
        """Gravitational potential is always negative."""
        for r in [R_SUN, AU, 10 * AU]:
            assert gravitational_potential_sun(r) < 0

    def test_potential_inverse_distance(self):
        """Potential scales as 1/r."""
        phi_1 = gravitational_potential_sun(AU)
        phi_2 = gravitational_potential_sun(2 * AU)
        assert phi_1 / phi_2 == pytest.approx(2.0, rel=1e-10)


class TestProperTimeIntegration:
    @pytest.fixture
    def straight_worldline(self):
        """A 2-point straight-line worldline at 0.6c for 1 year (for SR test)."""
        beta = 0.6
        speed = beta * c
        dt = YEAR
        coord_times = np.array([0.0, dt])
        positions = np.array([
            [AU, 0.0, 0.0],
            [AU + speed * dt, 0.0, 0.0],
        ])
        proper_times = np.array([0.0, dt * np.sqrt(1.0 - beta**2)])
        return Worldline(coord_times=coord_times, positions=positions, proper_times=proper_times)

    @pytest.fixture
    def orbital_worldline(self):
        """A multi-segment worldline at low speed circling at ~1 AU for 1 year.

        Uses low beta so the orbit can be well-sampled with 200 points.
        """
        beta = 0.001
        speed = beta * c
        dt = YEAR
        n_points = 500
        ct = np.linspace(0, dt, n_points)
        # Circle at radius 1 AU
        angle_rate = speed / AU
        positions = np.zeros((n_points, 3))
        positions[:, 0] = AU * np.cos(angle_rate * ct)
        positions[:, 1] = AU * np.sin(angle_rate * ct)
        proper_times = ct * np.sqrt(1.0 - beta**2)
        return Worldline(coord_times=ct, positions=positions, proper_times=proper_times)

    def test_sr_proper_time(self, straight_worldline):
        """SR proper time for 0.6c over 1 year."""
        from math import sqrt
        expected = YEAR * sqrt(1.0 - 0.6**2)
        result = sr_proper_time(straight_worldline)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_gr_tau_less_than_sr_tau(self, orbital_worldline):
        """GR proper time < SR proper time (gravity slows clocks further)."""
        sr_tau = sr_proper_time(orbital_worldline)
        gr_tau, _, _, _ = gr_corrected_proper_time(orbital_worldline)
        assert gr_tau < sr_tau

    def test_gr_correction_magnitude_at_1au(self, orbital_worldline):
        """GR correction for trajectory at ~1 AU: relative ~r_s/(2r) ≈ 1e-8."""
        diag = gr_correction(orbital_worldline)
        # Relative correction should be ~r_s/(2r) ≈ 1e-8
        assert diag.relative_correction == pytest.approx(1e-8, rel=5.0)
        # Absolute correction for 1 year at 1 AU: ~0.3 s
        assert abs(diag.delta_tau_s) > 0.01
        assert abs(diag.delta_tau_s) < 10.0

    def test_gr_diagnostics_fields(self, orbital_worldline):
        """GR diagnostics dataclass has all expected fields."""
        diag = gr_correction(orbital_worldline)
        assert isinstance(diag, GRDiagnostics)
        assert diag.sr_proper_time_s > 0
        assert diag.gr_proper_time_s > 0
        assert diag.delta_tau_s < 0  # GR clocks slower
        assert diag.relative_correction > 0
        assert diag.min_distance_from_sun_m > 0
        assert diag.max_gravitational_dilation > 0
        assert len(diag.gr_factor_profile) > 0


class TestMultiSegmentWorldline:
    def test_finer_worldline_matches(self):
        """Finer segmentation gives similar result."""
        beta = 0.3
        speed = beta * c
        dt_total = 2 * YEAR
        n_points = 100
        ct = np.linspace(0, dt_total, n_points)
        positions = np.zeros((n_points, 3))
        positions[:, 0] = AU + speed * ct  # along x-axis near 1 AU
        proper_times = ct * np.sqrt(1.0 - beta**2)

        wl = Worldline(coord_times=ct, positions=positions, proper_times=proper_times)
        diag = gr_correction(wl)

        # Relative correction should be ~r_s/(2*r) ≈ 1e-8
        assert diag.relative_correction == pytest.approx(1e-8, rel=5.0)
        assert diag.delta_tau_s < 0
