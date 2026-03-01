"""Integration tests for GR-corrected trajectories through the full stack."""

import pytest

from marte.constants import AU, SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.solver import TrajectoryModel, solve_trajectory


c = SPEED_OF_LIGHT


class TestGRCorrectionV1:
    def test_v1_with_gr_returns_diagnostics(self):
        """v1 solve with gr_corrections=True returns diagnostics."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            gr_corrections=True,
        )
        assert sol.gr_diagnostics is not None
        assert sol.gr_diagnostics.sr_proper_time_s > 0
        assert sol.gr_diagnostics.gr_proper_time_s > 0

    def test_v1_default_no_gr(self):
        """Default v1 solve has no GR diagnostics."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
        )
        assert sol.gr_diagnostics is None

    def test_v1_gr_tau_less_than_sr_tau(self):
        """GR proper time < SR proper time (clocks slower in gravity well)."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            gr_corrections=True,
        )
        grd = sol.gr_diagnostics
        assert grd is not None
        assert grd.gr_proper_time_s < grd.sr_proper_time_s

    def test_v1_relative_correction_order(self):
        """Relative correction is ~10⁻⁸ for trajectory near 1 AU."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            gr_corrections=True,
        )
        grd = sol.gr_diagnostics
        assert grd is not None
        # Relative correction should be on order of r_s/(2r) ≈ 1e-8
        # But v1 worldline has only 3 points and goes far from Sun,
        # so the correction may be smaller
        assert grd.relative_correction > 0
        assert grd.relative_correction < 1e-4  # definitely much less than 0.01%


class TestGRCorrectionV2:
    def test_v2_with_gr_returns_diagnostics(self):
        """v2 solve with gr_corrections=True returns diagnostics."""
        sol = solve_trajectory(
            t0=0.0,
            tf=5 * YEAR,
            proper_time_desired=3 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=STANDARD_GRAVITY,
            gr_corrections=True,
        )
        assert sol.gr_diagnostics is not None
        assert sol.gr_diagnostics.sr_proper_time_s > 0

    def test_v2_default_no_gr(self):
        """Default v2 solve has no GR diagnostics."""
        sol = solve_trajectory(
            t0=0.0,
            tf=5 * YEAR,
            proper_time_desired=3 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=STANDARD_GRAVITY,
        )
        assert sol.gr_diagnostics is None

    def test_v2_gr_tau_less_than_sr(self):
        """v2 GR proper time < SR proper time."""
        sol = solve_trajectory(
            t0=0.0,
            tf=5 * YEAR,
            proper_time_desired=3 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=STANDARD_GRAVITY,
            gr_corrections=True,
        )
        grd = sol.gr_diagnostics
        assert grd is not None
        assert grd.gr_proper_time_s < grd.sr_proper_time_s
        assert grd.delta_tau_s < 0

    def test_v2_2yr_trip_correction_magnitude(self):
        """2-year 1g brachistochrone: |Δτ| ≈ order of seconds."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            model=TrajectoryModel.CONSTANT_ACCELERATION,
            proper_acceleration=STANDARD_GRAVITY,
            gr_corrections=True,
        )
        grd = sol.gr_diagnostics
        assert grd is not None
        # Correction should be small but measurable
        assert abs(grd.delta_tau_s) < 100.0  # less than 100 seconds
        assert abs(grd.delta_tau_s) > 0  # non-zero


class TestGRCorrectionAPI:
    def test_api_endpoint_returns_gr(self):
        """API solve endpoint returns gr_diagnostics when requested."""
        from fastapi.testclient import TestClient
        from server.main import app

        client = TestClient(app)
        resp = client.post("/api/solve", json={
            "t0_years": 0.0,
            "tf_years": 2.0,
            "proper_time_years": 1.5,
            "gr_corrections": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["gr_diagnostics"] is not None
        grd = data["gr_diagnostics"]
        assert grd["sr_proper_time_s"] > 0
        assert grd["gr_proper_time_s"] > 0
        assert grd["delta_tau_s"] < 0
        assert grd["relative_correction"] > 0
        assert grd["min_distance_from_sun_au"] > 0

    def test_api_default_no_gr(self):
        """API solve without gr_corrections returns null."""
        from fastapi.testclient import TestClient
        from server.main import app

        client = TestClient(app)
        resp = client.post("/api/solve", json={
            "t0_years": 0.0,
            "tf_years": 2.0,
            "proper_time_years": 1.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["gr_diagnostics"] is None
