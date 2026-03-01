"""Tests for ephemeris module — time conversions, parsing, and earth_model threading."""

import numpy as np
import pytest

from marte.constants import AU, J2000_JD, YEAR
from marte.ephemeris import (
    EphemerisData,
    jd_to_marte_time,
    marte_time_to_calendar,
    marte_time_to_jd,
)
from marte.orbital import (
    _resolve_earth_model,
    earth_position,
    earth_velocity,
    set_ephemeris,
)


class TestTimeConversions:
    def test_jd_roundtrip(self):
        """JD conversions round-trip correctly."""
        t_s = 1e7  # ~115 days
        jd = marte_time_to_jd(t_s)
        t_back = jd_to_marte_time(jd)
        # Floating-point limits: JD ~2.45e6 days * 86400 → ~1e-3 s precision
        assert t_back == pytest.approx(t_s, abs=0.01)

    def test_j2000_epoch(self):
        """t=0 maps to J2000.0."""
        jd = marte_time_to_jd(0.0)
        assert jd == pytest.approx(J2000_JD, abs=1e-10)

    def test_one_year_from_j2000(self):
        """t=1 year maps to JD = J2000 + 365.25."""
        jd = marte_time_to_jd(YEAR)
        expected = J2000_JD + 365.25
        assert jd == pytest.approx(expected, abs=1e-6)

    def test_calendar_at_j2000(self):
        """t=0 gives approximately 2000-01-01."""
        cal = marte_time_to_calendar(0.0)
        assert cal.startswith("2000-01-01")

    def test_calendar_one_year(self):
        """t=1 year gives approximately end of 2000 / start of 2001."""
        cal = marte_time_to_calendar(YEAR)
        # J2000.0 is Jan 1.5, 2000; + 365.25 days → Dec 31, 2000 (or Jan 1, 2001)
        assert cal.startswith("2000-12") or cal.startswith("2001-01")

    def test_negative_time(self):
        """Negative MARTE time gives JD before J2000."""
        jd = marte_time_to_jd(-YEAR)
        assert jd < J2000_JD


class TestEphemerisData:
    @pytest.fixture
    def sinusoidal_ephemeris(self):
        """Create EphemerisData from a sinusoidal orbit with dense sampling."""
        n = 500
        times = np.linspace(0, 2 * YEAR, n)
        omega = 2 * np.pi / YEAR
        positions = np.zeros((n, 3))
        positions[:, 0] = AU * np.cos(omega * times)
        positions[:, 1] = AU * np.sin(omega * times)
        velocities = np.zeros((n, 3))
        velocities[:, 0] = -AU * omega * np.sin(omega * times)
        velocities[:, 1] = AU * omega * np.cos(omega * times)
        return EphemerisData(times_s=times, positions_m=positions, velocities_m_s=velocities)

    def test_interpolation_sinusoidal(self, sinusoidal_ephemeris):
        """EphemerisData interpolation works against known sinusoidal data."""
        omega = 2 * np.pi / YEAR
        # Interpolate at 1/3 orbit where both components are well away from zero
        t_query = YEAR / 3.0
        pos = sinusoidal_ephemeris.position(t_query)
        expected_x = AU * np.cos(omega * t_query)
        expected_y = AU * np.sin(omega * t_query)
        assert pos[0] == pytest.approx(expected_x, rel=1e-3)
        assert pos[1] == pytest.approx(expected_y, rel=1e-3)

    def test_velocity_interpolation(self, sinusoidal_ephemeris):
        """EphemerisData velocity interpolation works."""
        omega = 2 * np.pi / YEAR
        t_query = YEAR / 3.0
        vel = sinusoidal_ephemeris.velocity(t_query)
        expected_vx = -AU * omega * np.sin(omega * t_query)
        expected_vy = AU * omega * np.cos(omega * t_query)
        assert vel[0] == pytest.approx(expected_vx, rel=1e-2)
        assert vel[1] == pytest.approx(expected_vy, rel=1e-2)


class TestEarthModelResolution:
    def test_circular_default(self):
        """Default resolves to 'circular'."""
        assert _resolve_earth_model(False, None) == "circular"

    def test_elliptical_bool(self):
        """elliptical=True resolves to 'elliptical'."""
        assert _resolve_earth_model(True, None) == "elliptical"

    def test_string_overrides_bool(self):
        """earth_model string overrides elliptical bool."""
        assert _resolve_earth_model(True, "circular") == "circular"
        assert _resolve_earth_model(False, "elliptical") == "elliptical"
        assert _resolve_earth_model(False, "ephemeris") == "ephemeris"

    def test_circular_matches_default(self):
        """earth_model='circular' gives same result as default."""
        t = YEAR / 2.0
        pos_default = earth_position(t)
        pos_circular = earth_position(t, earth_model="circular")
        np.testing.assert_array_almost_equal(pos_default, pos_circular)

    def test_elliptical_matches_bool(self):
        """earth_model='elliptical' gives same result as elliptical=True."""
        t = YEAR / 2.0
        pos_bool = earth_position(t, elliptical=True)
        pos_str = earth_position(t, earth_model="elliptical")
        np.testing.assert_array_almost_equal(pos_bool, pos_str)

    def test_velocity_circular_matches_default(self):
        """earth_velocity with earth_model='circular' matches default."""
        t = YEAR / 4.0
        vel_default = earth_velocity(t)
        vel_circular = earth_velocity(t, earth_model="circular")
        np.testing.assert_array_almost_equal(vel_default, vel_circular)


class TestEphemerisModel:
    def test_ephemeris_with_injected_data(self):
        """earth_model='ephemeris' works with injected EphemerisData."""
        # Create synthetic ephemeris that matches circular orbit
        n = 50
        times = np.linspace(0, 2 * YEAR, n)
        omega = 2 * np.pi / YEAR
        positions = np.zeros((n, 3))
        positions[:, 0] = AU * np.cos(omega * times)
        positions[:, 1] = AU * np.sin(omega * times)
        velocities = np.zeros((n, 3))
        velocities[:, 0] = -AU * omega * np.sin(omega * times)
        velocities[:, 1] = AU * omega * np.cos(omega * times)

        eph = EphemerisData(times_s=times, positions_m=positions, velocities_m_s=velocities)
        set_ephemeris(eph)

        # Should match circular model approximately
        t = YEAR / 4.0
        pos_eph = earth_position(t, earth_model="ephemeris")
        pos_circ = earth_position(t, earth_model="circular")
        # Within 1% since they use the same underlying model
        assert np.linalg.norm(pos_eph - pos_circ) / np.linalg.norm(pos_circ) < 0.01

    def test_ephemeris_without_data_raises(self):
        """earth_model='ephemeris' raises error when no data loaded."""
        set_ephemeris(None)  # type: ignore[arg-type]
        # Reset cached ephemeris
        import marte.orbital
        marte.orbital._cached_ephemeris = None
        with pytest.raises(RuntimeError, match="Ephemeris data not loaded"):
            earth_position(0.0, earth_model="ephemeris")
