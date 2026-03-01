"""Tests for parameter sweeps (Phase 5, Chunk 3)."""

import numpy as np
from fastapi.testclient import TestClient

from marte.sweep import sweep_1d, sweep_2d
from server.main import app

client = TestClient(app)


BASE_PARAMS = {
    "t0_years": 0.0,
    "tf_years": 2.0,
    "proper_time_years": 1.5,
    "mass_kg": 1000.0,
    "trajectory_model": "constant_velocity",
}


def test_sweep_1d_correct_number_of_points():
    """1D sweep returns correct number of points."""
    values = np.linspace(1.0, 5.0, 10).tolist()
    result = sweep_1d(BASE_PARAMS, "tf_years", values)
    assert len(result.points) == 10
    assert result.swept_param == "tf_years"


def test_sweep_1d_converged_have_valid_energy():
    """All converged points have valid energy values."""
    values = np.linspace(2.0, 5.0, 5).tolist()
    result = sweep_1d(BASE_PARAMS, "tf_years", values)
    for pt in result.points:
        if pt.converged:
            assert pt.energy is not None
            assert pt.energy > 0


def test_sweep_1d_failed_points():
    """Points where tau > delta_t are marked as not converged."""
    # proper_time_years = 1.5, sweep tf from 0.5 to 1.0 (all < tau)
    values = np.linspace(0.5, 1.0, 5).tolist()
    result = sweep_1d(BASE_PARAMS, "tf_years", values)
    for pt in result.points:
        assert not pt.converged


def test_sweep_2d_correct_dimensions():
    """2D sweep returns grid of correct dimensions."""
    x_vals = np.linspace(2.0, 4.0, 3).tolist()
    y_vals = np.linspace(0.5, 1.5, 3).tolist()
    result = sweep_2d(BASE_PARAMS, "tf_years", x_vals, "proper_time_years", y_vals)
    assert len(result.grid) == 3  # y
    assert len(result.grid[0]) == 3  # x


def test_sweep_1d_api():
    """API 1D sweep endpoint returns correct schema."""
    resp = client.post("/api/sweep/1d", json={
        "base_params": BASE_PARAMS,
        "param_name": "tf_years",
        "min_value": 2.0,
        "max_value": 5.0,
        "steps": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["swept_param"] == "tf_years"
    assert len(data["points"]) == 5


def test_sweep_2d_api():
    """API 2D sweep endpoint returns correct schema."""
    resp = client.post("/api/sweep/2d", json={
        "base_params": BASE_PARAMS,
        "x_param": "tf_years",
        "x_min": 2.0,
        "x_max": 4.0,
        "y_param": "proper_time_years",
        "y_min": 0.5,
        "y_max": 1.5,
        "x_steps": 3,
        "y_steps": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["x_param"] == "tf_years"
    assert data["y_param"] == "proper_time_years"
    assert len(data["points"]) == 9  # 3x3
    assert data["x_steps"] == 3
    assert data["y_steps"] == 3


def test_sweep_with_multi_target():
    """Sweep with multi-target works."""
    params = {**BASE_PARAMS, "target": "mars", "tf_years": 1.5, "proper_time_years": 1.2}
    values = np.linspace(1.5, 3.0, 3).tolist()
    result = sweep_1d(params, "tf_years", values, target="mars")
    assert len(result.points) == 3


def test_sweep_1d_steps_capped():
    """Steps capped at 50 for 1D sweeps."""
    resp = client.post("/api/sweep/1d", json={
        "base_params": BASE_PARAMS,
        "param_name": "tf_years",
        "min_value": 2.0,
        "max_value": 5.0,
        "steps": 50,  # max
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 50


def test_sweep_2d_steps_capped():
    """Steps capped at 30x30 for 2D sweeps."""
    resp = client.post("/api/sweep/2d", json={
        "base_params": BASE_PARAMS,
        "x_param": "tf_years",
        "x_min": 2.0,
        "x_max": 4.0,
        "y_param": "proper_time_years",
        "y_min": 0.5,
        "y_max": 1.5,
        "x_steps": 30,
        "y_steps": 30,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 900  # 30x30
