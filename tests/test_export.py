"""Tests for data export (Phase 5, Chunk 2)."""

import csv
import io
import json

from fastapi.testclient import TestClient

from marte.constants import YEAR
from marte.export import export_csv, export_json, export_mission_report
from marte.solver import solve_trajectory
from server.main import app

client = TestClient(app)


def _get_solution():
    return solve_trajectory(0.0, 2.0 * YEAR, 1.5 * YEAR)


def test_json_export_contains_expected_fields():
    """JSON export contains inputs, results, and worldline."""
    sol = _get_solution()
    params = {"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 1.5}
    result = json.loads(export_json(sol, params))
    assert "inputs" in result
    assert "results" in result
    assert "worldline" in result
    assert result["results"]["converged"] is True
    assert "energy_joules" in result["results"]


def test_json_export_is_valid_json():
    """JSON export is parseable JSON."""
    sol = _get_solution()
    data = export_json(sol, {})
    parsed = json.loads(data)
    assert isinstance(parsed, dict)


def test_csv_has_correct_headers():
    """CSV has expected column headers."""
    sol = _get_solution()
    data = export_csv(sol)
    reader = csv.reader(io.StringIO(data))
    headers = next(reader)
    assert headers == [
        "coord_time_s", "proper_time_s",
        "x_m", "y_m", "z_m",
        "vx", "vy", "vz",
        "beta", "gamma",
    ]


def test_csv_row_count_matches_worldline():
    """CSV row count matches worldline length."""
    sol = _get_solution()
    data = export_csv(sol)
    reader = csv.reader(io.StringIO(data))
    next(reader)  # skip header
    rows = list(reader)
    assert len(rows) == len(sol.worldline.coord_times)


def test_export_with_gr_includes_diagnostics():
    """JSON export with GR corrections includes diagnostics."""
    sol = solve_trajectory(
        0.0, 2.0 * YEAR, 1.5 * YEAR,
        gr_corrections=True,
    )
    report = export_mission_report(sol, {"gr_corrections": True})
    assert "diagnostics" in report
    assert "gr" in report["diagnostics"]


def test_export_with_perturbation_includes_diagnostics():
    """JSON export with perturbation includes diagnostics."""
    sol = solve_trajectory(
        0.0, 2.0 * YEAR, 1.5 * YEAR,
        compute_perturbation=True,
    )
    report = export_mission_report(sol, {"compute_perturbation": True})
    assert "diagnostics" in report
    assert "perturbation" in report["diagnostics"]


def test_api_export_json_content_type():
    """POST /api/export/json returns application/json."""
    resp = client.post("/api/export/json", json={})
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "inputs" in data
    assert "results" in data


def test_api_export_csv_content_type():
    """POST /api/export/csv returns text/csv."""
    resp = client.post("/api/export/csv", json={})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().split("\n")
    assert len(lines) >= 2  # header + at least 1 data row


def test_export_with_multi_target():
    """Export with target info includes target in inputs."""
    sol = solve_trajectory(0.0, 1.5 * YEAR, 1.2 * YEAR, target="mars")
    params = {"target": "mars", "t0_years": 0.0, "tf_years": 1.5}
    report = export_mission_report(sol, params)
    assert report["inputs"]["target"] == "mars"
