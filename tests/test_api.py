"""Tests for the FastAPI server endpoints."""

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_solve_valid_default():
    resp = client.post("/api/solve", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is None
    assert data["solution"] is not None
    assert data["worldline"] is not None
    assert data["earth"] is not None
    assert data["solution"]["converged"] is True


def test_solve_valid_custom():
    resp = client.post(
        "/api/solve",
        json={
            "t0_years": 0.0,
            "tf_years": 2.0,
            "proper_time_years": 1.5,
            "mass_kg": 1000.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True


def test_solve_invalid_tau_ge_delta_t():
    resp = client.post(
        "/api/solve",
        json={"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 2.5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is not None
    assert data["solution"] is None
    assert "proper time" in data["error"].lower() or "Proper time" in data["error"]


def test_solve_invalid_negative_interval():
    resp = client.post(
        "/api/solve",
        json={"t0_years": 3.0, "tf_years": 1.0, "proper_time_years": 0.5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is not None
    assert data["solution"] is None


def test_response_schema_structure():
    resp = client.post("/api/solve", json={})
    data = resp.json()
    assert "inputs" in data
    assert "solution" in data
    assert "worldline" in data
    assert "earth" in data
    assert "error" in data

    sol = data["solution"]
    assert "beta" in sol
    assert "gamma" in sol
    assert "speed_m_s" in sol
    assert "energy_joules" in sol
    assert "converged" in sol
    assert "direction_out" in sol
    assert "direction_in" in sol

    wl = data["worldline"]
    assert "coord_times_s" in wl
    assert "coord_times_years" in wl
    assert "positions_m" in wl
    assert "positions_au" in wl
    assert "proper_times_s" in wl
    assert "proper_times_years" in wl

    earth = data["earth"]
    assert "orbit_radius_au" in earth
    assert "departure_position_au" in earth
    assert "arrival_position_au" in earth
    assert "trajectory_times_years" in earth
    assert "trajectory_positions_au" in earth


def test_numeric_accuracy():
    """Verify β, γ match expected values for t0=0, tf=2y, τ=1.5y."""
    resp = client.post(
        "/api/solve",
        json={"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 1.5},
    )
    data = resp.json()
    sol = data["solution"]

    # β = √(1 - (1.5/2)²) = √(1 - 0.5625) = √0.4375 ≈ 0.6614
    assert abs(sol["beta"] - 0.6614) < 0.001

    # γ = 1/√(1 - β²) = 2/1.5 ≈ 1.3333
    assert abs(sol["gamma"] - 1.3333) < 0.001

    # Proper time should match input
    assert abs(sol["total_proper_time_years"] - 1.5) < 0.001

    # Turnaround at midpoint
    assert abs(sol["turnaround_time_years"] - 1.0) < 0.001


def test_worldline_has_three_waypoints():
    resp = client.post("/api/solve", json={})
    data = resp.json()
    wl = data["worldline"]
    assert len(wl["coord_times_s"]) == 3
    assert len(wl["positions_m"]) == 3
    assert len(wl["proper_times_s"]) == 3


def test_earth_trajectory_sampling():
    resp = client.post("/api/solve", json={})
    data = resp.json()
    earth = data["earth"]
    assert len(earth["trajectory_times_years"]) == 100
    assert len(earth["trajectory_positions_au"]) == 100
    assert earth["orbit_radius_au"] == 1.0
