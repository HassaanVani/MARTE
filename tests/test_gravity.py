"""Tests for multi-body gravitational perturbation analysis."""

import numpy as np
import pytest

from marte.constants import (
    AU,
    GRAVITATIONAL_CONSTANT,
    JUPITER_ORBITAL_RADIUS,
    M_JUPITER,
    M_SATURN,
    SATURN_ORBITAL_RADIUS,
    SPEED_OF_LIGHT,
    STANDARD_GRAVITY,
    YEAR,
)
from marte.gravity import (
    compute_perturbation_profile,
    planetary_gravitational_acceleration,
    planetary_position,
    solar_gravitational_acceleration,
)
from marte.solver import TrajectoryModel, solve_trajectory
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT


class TestSolarGravity:
    def test_gravity_at_1au(self):
        """Solar gravity at 1 AU ≈ 5.93e-3 m/s² (0.0006 g)."""
        pos = np.array([AU, 0.0, 0.0])
        accel = solar_gravitational_acceleration(pos)
        mag = float(np.linalg.norm(accel))
        assert mag == pytest.approx(5.93e-3, rel=0.01)
        assert mag / STANDARD_GRAVITY == pytest.approx(6e-4, rel=0.1)

    def test_inverse_square_law(self):
        """Gravity falls off as 1/r²."""
        pos1 = np.array([AU, 0.0, 0.0])
        pos2 = np.array([2 * AU, 0.0, 0.0])
        a1 = float(np.linalg.norm(solar_gravitational_acceleration(pos1)))
        a2 = float(np.linalg.norm(solar_gravitational_acceleration(pos2)))
        assert a1 / a2 == pytest.approx(4.0, rel=1e-6)

    def test_points_toward_sun(self):
        """Gravitational acceleration points toward the Sun (origin)."""
        pos = np.array([AU, 0.0, 0.0])
        accel = solar_gravitational_acceleration(pos)
        # Acceleration should be in -x direction
        assert accel[0] < 0
        assert abs(accel[1]) < 1e-20
        assert abs(accel[2]) < 1e-20

    def test_gravity_at_various_distances(self):
        """Gravity varies correctly at different distances."""
        for r_au in [0.5, 1.0, 2.0, 5.0, 10.0]:
            pos = np.array([r_au * AU, 0.0, 0.0])
            accel = solar_gravitational_acceleration(pos)
            mag = float(np.linalg.norm(accel))
            assert mag > 0


class TestPlanetaryPositions:
    def test_jupiter_at_t0(self):
        """Jupiter position at t=0."""
        pos = planetary_position("jupiter", 0.0)
        assert pos[0] == pytest.approx(JUPITER_ORBITAL_RADIUS, rel=1e-6)
        assert abs(pos[1]) < 1.0
        assert abs(pos[2]) < 1.0

    def test_saturn_at_t0(self):
        """Saturn position at t=0."""
        pos = planetary_position("saturn", 0.0)
        assert pos[0] == pytest.approx(SATURN_ORBITAL_RADIUS, rel=1e-6)
        assert abs(pos[1]) < 1.0

    def test_jupiter_orbit_radius(self):
        """Jupiter maintains correct orbital radius at various times."""
        for t in [0, YEAR, 5 * YEAR, 10 * YEAR]:
            pos = planetary_position("jupiter", t)
            r = float(np.linalg.norm(pos))
            assert r == pytest.approx(JUPITER_ORBITAL_RADIUS, rel=1e-6)

    def test_unknown_body_raises(self):
        """Unknown body name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown body"):
            planetary_position("pluto", 0.0)


class TestPlanetaryGravity:
    def test_jupiter_gravity_at_1au(self):
        """Jupiter's gravity at 1 AU distance from Jupiter."""
        # Ship at origin, Jupiter at its orbital radius
        ship_pos = np.array([0.0, 0.0, 0.0])
        accel = planetary_gravitational_acceleration("jupiter", ship_pos, 0.0)
        mag = float(np.linalg.norm(accel))
        # GM_J / r² where r = Jupiter orbital radius
        gm_j = GRAVITATIONAL_CONSTANT * M_JUPITER
        expected = gm_j / JUPITER_ORBITAL_RADIUS**2
        assert mag == pytest.approx(expected, rel=0.01)


class TestSunDominates:
    def test_sun_dominates_at_1au(self):
        """Sun's gravity dominates over Jupiter and Saturn at 1 AU."""
        pos = np.array([AU, 0.0, 0.0])
        t = 0.0
        a_sun = float(np.linalg.norm(solar_gravitational_acceleration(pos)))
        a_jup = float(np.linalg.norm(
            planetary_gravitational_acceleration("jupiter", pos, t)))
        a_sat = float(np.linalg.norm(
            planetary_gravitational_acceleration("saturn", pos, t)))
        assert a_sun > a_jup * 100  # Sun >> Jupiter
        assert a_sun > a_sat * 1000  # Sun >> Saturn


class TestPerturbationProfile:
    @pytest.fixture
    def simple_worldline(self):
        """A worldline at 0.3c near 1 AU for 1 year."""
        beta = 0.3
        speed = beta * c
        n = 50
        ct = np.linspace(0, YEAR, n)
        positions = np.zeros((n, 3))
        # Travel along x at ~1 AU
        positions[:, 0] = AU + speed * ct
        proper_times = ct * np.sqrt(1.0 - beta**2)
        return Worldline(coord_times=ct, positions=positions, proper_times=proper_times)

    def test_perturbation_profile_fields(self, simple_worldline):
        """PerturbationAnalysis has all expected fields."""
        pa = compute_perturbation_profile(simple_worldline)
        assert pa.max_accel_sun > 0
        assert pa.max_accel_jupiter > 0
        assert pa.max_accel_saturn > 0
        assert pa.total_delta_v_sun > 0
        assert pa.total_delta_v_jupiter > 0
        assert pa.total_delta_v_saturn > 0
        assert pa.closest_approach_sun > 0
        assert pa.closest_approach_jupiter > 0
        assert pa.closest_approach_saturn > 0

    def test_sun_max_accel_order(self, simple_worldline):
        """Sun's max acceleration ≈ 5.93e-3 m/s² at 1 AU."""
        pa = compute_perturbation_profile(simple_worldline)
        # Ship starts at 1 AU, so max solar accel is ~5.93e-3
        assert pa.max_accel_sun == pytest.approx(5.93e-3, rel=0.5)

    def test_sun_dominates_perturbation(self, simple_worldline):
        """Sun provides the dominant perturbation."""
        pa = compute_perturbation_profile(simple_worldline)
        assert pa.total_delta_v_sun > pa.total_delta_v_jupiter * 10
        assert pa.total_delta_v_sun > pa.total_delta_v_saturn * 10


class TestPerturbationThroughSolver:
    def test_solver_perturbation_default_off(self):
        """Perturbation analysis is off by default."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
        )
        assert sol.perturbation is None

    def test_solver_perturbation_on(self):
        """Perturbation analysis works when enabled."""
        sol = solve_trajectory(
            t0=0.0,
            tf=2 * YEAR,
            proper_time_desired=1.5 * YEAR,
            compute_perturbation=True,
        )
        assert sol.perturbation is not None
        assert sol.perturbation.max_accel_sun > 0


class TestPerturbationAPI:
    def test_api_perturbation_schema(self):
        """API returns perturbation data when requested."""
        from fastapi.testclient import TestClient
        from server.main import app

        client = TestClient(app)
        resp = client.post("/api/solve", json={
            "t0_years": 0.0,
            "tf_years": 2.0,
            "proper_time_years": 1.5,
            "compute_perturbation": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["perturbation"] is not None
        p = data["perturbation"]
        assert p["max_accel_sun_m_s2"] > 0
        assert p["max_accel_jupiter_m_s2"] > 0
        assert p["max_accel_saturn_m_s2"] > 0

    def test_api_perturbation_default_off(self):
        """API returns no perturbation data by default."""
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
        assert data["perturbation"] is None
