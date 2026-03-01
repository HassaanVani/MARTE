"""Integration tests for Phase 5 (Navigation Console)."""

import json

from fastapi.testclient import TestClient

from marte.constants import YEAR
from marte.export import export_csv, export_json
from marte.optimization import compute_pareto_front
from marte.solver import solve_trajectory
from marte.sweep import sweep_1d
from marte.targets import list_targets
from server.main import app

client = TestClient(app)


def test_end_to_end_mars_solve_export():
    """End-to-end: solve with target='mars', export JSON, verify target info."""
    sol = solve_trajectory(0.0, 1.5 * YEAR, 1.2 * YEAR, target="mars")
    params = {"target": "mars", "t0_years": 0.0, "tf_years": 1.5}
    data = json.loads(export_json(sol, params))
    assert data["inputs"]["target"] == "mars"
    assert data["results"]["converged"] is True
    assert data["worldline"]["n_points"] >= 3


def test_sweep_1d_then_export_csv():
    """Sweep 1D + verify first converged solution can be exported to CSV."""
    import numpy as np
    values = np.linspace(2.0, 4.0, 5).tolist()
    result = sweep_1d(
        {"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 1.5,
         "mass_kg": 1000.0, "trajectory_model": "constant_velocity"},
        "tf_years", values,
    )
    # Find a converged point and verify its params can be used
    converged = [p for p in result.points if p.converged]
    assert len(converged) > 0
    # Export the first converged solution
    sol = solve_trajectory(0.0, converged[0].params["tf_years"] * YEAR, 1.5 * YEAR)
    csv_data = export_csv(sol)
    lines = csv_data.strip().split("\n")
    assert len(lines) >= 2  # header + data


def test_pareto_for_mars_transfer():
    """Pareto front for Mars transfer."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        target="mars",
        n_points=20,
    )
    assert front.target == "mars"
    assert len(front.points) >= 5
    # Verify energy decreases with proper time
    if len(front.points) >= 2:
        assert front.points[0].energy_joules > front.points[-1].energy_joules


def test_api_targets_returns_all():
    """API /api/targets returns all 5 targets."""
    resp = client.get("/api/targets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    names = {t["name"] for t in data}
    assert names == {"Earth", "Mercury", "Venus", "Mars", "Jupiter"}


def test_all_targets_available():
    """list_targets returns all 5 target names."""
    targets = list_targets()
    assert set(targets) == {"earth", "mercury", "venus", "mars", "jupiter"}


def test_backward_compat_existing_solve():
    """Existing features still work: default solve returns valid response."""
    resp = client.post("/api/solve", json={})
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    assert data["solution"]["trajectory_model"] == "constant_velocity"


def test_backward_compat_v2_solve():
    """Existing v2 features still work."""
    resp = client.post("/api/solve", json={
        "trajectory_model": "constant_acceleration",
        "proper_acceleration_g": 1.0,
        "tf_years": 5.0,
        "proper_time_years": 4.0,
    })
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    assert data["solution"]["peak_beta"] is not None


def test_backward_compat_gr_perturbation():
    """GR and perturbation features still work."""
    resp = client.post("/api/solve", json={
        "gr_corrections": True,
        "compute_perturbation": True,
    })
    data = resp.json()
    assert data["error"] is None
    assert data["gr_diagnostics"] is not None
    assert data["perturbation"] is not None


def test_full_pipeline_target_solve_sweep_pareto_export():
    """Full pipeline: solve + sweep + pareto + export for Mars."""
    # 1. Solve
    resp = client.post("/api/solve", json={
        "target": "mars",
        "tf_years": 1.5,
        "proper_time_years": 1.2,
    })
    assert resp.status_code == 200
    solve_data = resp.json()
    assert solve_data["solution"] is not None

    # 2. Sweep 1D
    resp = client.post("/api/sweep/1d", json={
        "base_params": {
            "target": "mars",
            "tf_years": 1.5,
            "proper_time_years": 1.2,
        },
        "param_name": "tf_years",
        "min_value": 1.5,
        "max_value": 3.0,
        "steps": 5,
    })
    assert resp.status_code == 200
    sweep_data = resp.json()
    assert len(sweep_data["points"]) == 5

    # 3. Pareto
    resp = client.post("/api/pareto", json={
        "target": "mars",
        "tf_years": 2.0,
        "n_points": 10,
    })
    assert resp.status_code == 200
    pareto_data = resp.json()
    assert len(pareto_data["points"]) >= 3

    # 4. Export JSON
    resp = client.post("/api/export/json", json={
        "target": "mars",
        "tf_years": 1.5,
        "proper_time_years": 1.2,
    })
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]

    # 5. Export CSV
    resp = client.post("/api/export/csv", json={
        "target": "mars",
        "tf_years": 1.5,
        "proper_time_years": 1.2,
    })
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
