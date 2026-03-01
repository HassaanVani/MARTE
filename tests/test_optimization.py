"""Tests for Pareto front optimization (Phase 5, Chunk 4)."""

from fastapi.testclient import TestClient

from marte.constants import STANDARD_GRAVITY, YEAR
from marte.optimization import compute_pareto_front
from server.main import app

client = TestClient(app)


def test_pareto_returns_at_least_10_points():
    """Pareto front returns at least 10 points for default params."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        n_points=50,
    )
    assert len(front.points) >= 10


def test_pareto_sorted_by_proper_time():
    """Points are sorted by proper_time ascending."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        n_points=30,
    )
    taus = [p.proper_time_years for p in front.points]
    assert taus == sorted(taus)


def test_pareto_energy_decreases_with_proper_time():
    """Energy generally decreases as proper_time increases."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        n_points=30,
    )
    if len(front.points) >= 2:
        # First point (low tau, high dilation) should have more energy
        # than last point (high tau, low dilation)
        assert front.points[0].energy_joules > front.points[-1].energy_joules


def test_pareto_no_duplicate_tau_points():
    """No two points share the same proper time (duplicates removed)."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        n_points=30,
    )
    taus = [p.proper_time_years for p in front.points]
    # All tau values should be distinct (within tolerance)
    for i in range(len(taus) - 1):
        assert abs(taus[i + 1] - taus[i]) > 1e-6, f"Duplicate tau at index {i}"


def test_pareto_with_constant_acceleration():
    """Works with constant_acceleration model."""
    front = compute_pareto_front(
        t0=0.0,
        tf=5.0 * YEAR,
        mass=1000.0,
        model="constant_acceleration",
        proper_acceleration=STANDARD_GRAVITY,
        n_points=20,
    )
    # Should get at least some points
    assert len(front.points) >= 5


def test_pareto_with_multi_target():
    """Works with multi-target (Mars)."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        target="mars",
        n_points=20,
    )
    assert front.target == "mars"
    assert len(front.points) >= 5


def test_pareto_api_endpoint():
    """API endpoint returns correct schema."""
    resp = client.post("/api/pareto", json={
        "t0_years": 0.0,
        "tf_years": 2.0,
        "mass_kg": 1000.0,
        "n_points": 20,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "points" in data
    assert "target" in data
    assert len(data["points"]) >= 5
    for pt in data["points"]:
        assert "proper_time_years" in pt
        assert "energy_joules" in pt
        assert "peak_beta" in pt


def test_pareto_n_points_capped():
    """n_points capped at 100."""
    front = compute_pareto_front(
        t0=0.0,
        tf=2.0 * YEAR,
        mass=1000.0,
        n_points=200,  # exceeds cap
    )
    # Should still work (internally capped)
    assert len(front.points) <= 100
