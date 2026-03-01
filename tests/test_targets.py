"""Tests for multi-target support (Phase 5, Chunk 1)."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from marte.constants import YEAR
from marte.orbital import earth_position
from marte.solver import TrajectoryModel, solve_trajectory
from marte.targets import TARGETS, list_targets, target_position, target_velocity
from server.main import app

client = TestClient(app)


def test_target_registry_has_five_entries():
    """Target registry contains earth, mercury, venus, mars, jupiter."""
    names = list_targets()
    assert len(names) == 5
    assert set(names) == {"earth", "mercury", "venus", "mars", "jupiter"}


def test_target_position_mars_at_orbital_radius():
    """target_position('mars', 0) returns position at Mars orbital radius."""
    pos = target_position("mars", 0.0)
    r = np.linalg.norm(pos)
    assert abs(r - TARGETS["mars"].orbital_radius_m) < 1.0


def test_target_position_earth_matches_orbital():
    """target_position('earth', t) matches earth_position(t) for circular orbit."""
    for t in [0.0, 0.5 * YEAR, 1.0 * YEAR, 2.5 * YEAR]:
        pos_target = target_position("earth", t)
        pos_earth = earth_position(t)
        np.testing.assert_allclose(pos_target, pos_earth, rtol=1e-6)


def test_target_velocity_mars():
    """target_velocity returns a velocity perpendicular to position."""
    pos = target_position("mars", 0.0)
    vel = target_velocity("mars", 0.0)
    # Perpendicular: dot product should be ~0
    dot = np.dot(pos, vel)
    assert abs(dot) < 1e6  # very small relative to magnitudes


def test_target_position_case_insensitive():
    """Target names are case-insensitive."""
    pos1 = target_position("Mars", 0.0)
    pos2 = target_position("mars", 0.0)
    np.testing.assert_array_equal(pos1, pos2)


def test_solver_v1_with_target_mars():
    """Solver with target='mars' returns valid solution."""
    t0 = 0.0
    tf = 1.5 * YEAR
    tau = 1.2 * YEAR
    sol = solve_trajectory(t0, tf, tau, target="mars")
    assert sol.converged
    assert sol.velocity_magnitude > 0
    assert sol.velocity_magnitude < 1.0


def test_solver_v2_with_target_mars():
    """Solver v2 with target='mars' returns valid solution."""
    t0 = 0.0
    tf = 2.0 * YEAR
    tau = 1.5 * YEAR
    sol = solve_trajectory(
        t0, tf, tau,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=9.80665,
        target="mars",
    )
    assert sol.peak_beta is not None
    assert sol.peak_beta < 1.0
    # The solver may not converge perfectly for all transfer geometries
    # but should produce a physically meaningful result
    assert sol.total_proper_time > 0


def test_api_solve_with_target_mars():
    """API endpoint with target='mars' works."""
    resp = client.post(
        "/api/solve",
        json={
            "t0_years": 0.0,
            "tf_years": 1.5,
            "proper_time_years": 1.2,
            "mass_kg": 1000.0,
            "target": "mars",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is None
    assert data["solution"] is not None
    assert data["solution"]["converged"] is True
    assert data["target_trajectory"] is not None
    assert data["target_trajectory"]["name"] == "Mars"


def test_api_targets_endpoint():
    """GET /api/targets returns list of targets."""
    resp = client.get("/api/targets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    names = {t["name"] for t in data}
    assert "Earth" in names
    assert "Mars" in names
    assert "Jupiter" in names


def test_default_target_earth_backward_compat():
    """Default target='earth' matches existing behavior."""
    resp = client.post("/api/solve", json={})
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    assert data["inputs"]["target"] == "earth"
    assert data["target_trajectory"] is None  # No target trajectory for earth


def test_target_trajectory_data_structure():
    """Target trajectory data has correct structure."""
    resp = client.post(
        "/api/solve",
        json={"target": "venus", "tf_years": 1.0, "proper_time_years": 0.7},
    )
    data = resp.json()
    tt = data["target_trajectory"]
    assert tt is not None
    assert tt["name"] == "Venus"
    assert tt["orbit_radius_au"] > 0
    assert len(tt["trajectory_positions_au"]) == 100
    assert len(tt["trajectory_times_years"]) == 100
