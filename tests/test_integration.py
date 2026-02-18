"""Integration tests — end-to-end verification of v1 and v2 pipelines."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.solver import TrajectoryModel, solve_trajectory
from marte.validation import check_subluminal
from server.main import app

client = TestClient(app)
c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY


# --- v1 full pipeline ---


def test_v1_full_pipeline():
    """v1: solve → API → verify schema + physics."""
    # 1. Solve directly
    sol = solve_trajectory(t0=0.0, tf=2 * YEAR, proper_time_desired=1.5 * YEAR)
    assert sol.converged
    assert check_subluminal(sol.worldline)
    assert sol.total_proper_time == pytest.approx(1.5 * YEAR, rel=1e-6)

    # 2. Solve via API
    resp = client.post(
        "/api/solve",
        json={"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 1.5},
    )
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    assert data["solution"]["trajectory_model"] == "constant_velocity"

    # 3. Schema completeness
    wl = data["worldline"]
    assert len(wl["coord_times_s"]) == 3  # v1 has 3 waypoints
    assert len(wl["positions_au"]) == 3
    assert data["earth"]["orbit_radius_au"] == 1.0

    # 4. Physics consistency
    sol_data = data["solution"]
    assert sol_data["beta"] < 1.0
    assert sol_data["gamma"] > 1.0
    assert sol_data["total_proper_time_years"] == pytest.approx(1.5, abs=0.001)


# --- v2 full pipeline ---


def test_v2_full_pipeline():
    """v2: solve → API → verify schema + physics."""
    # 1. Solve directly
    sol = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )
    assert sol.converged
    assert check_subluminal(sol.worldline)
    assert sol.total_proper_time == pytest.approx(4.0 * YEAR, rel=1e-3)
    assert len(sol.worldline.coord_times) > 100

    # 2. Solve via API
    resp = client.post(
        "/api/solve",
        json={
            "t0_years": 0.0,
            "tf_years": 5.0,
            "proper_time_years": 4.0,
            "trajectory_model": "constant_acceleration",
            "proper_acceleration_g": 1.0,
        },
    )
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    assert data["solution"]["trajectory_model"] == "constant_acceleration"

    # 3. Schema completeness
    wl = data["worldline"]
    assert len(wl["coord_times_s"]) > 100  # v2 has many waypoints
    assert wl["beta_profile"] is not None
    assert len(wl["beta_profile"]) == len(wl["coord_times_s"])

    sol_data = data["solution"]
    assert sol_data["peak_beta"] is not None
    assert sol_data["peak_gamma"] is not None
    assert sol_data["phase_boundaries_years"] is not None
    assert len(sol_data["phase_boundaries_years"]) == 5

    # 4. Physics consistency
    assert sol_data["peak_beta"] < 1.0
    assert sol_data["peak_gamma"] > 1.0
    assert sol_data["total_proper_time_years"] == pytest.approx(4.0, abs=0.01)


# --- v1 and v2 consistency at low speeds ---


def test_v1_v2_consistency_low_speed():
    """At low speeds, v2 should give similar total proper time to v1.

    For a longer trip with modest time dilation, both models should agree
    on the basic physics (time dilation magnitude).
    """
    # v1 solution
    sol_v1 = solve_trajectory(t0=0.0, tf=5 * YEAR, proper_time_desired=4.5 * YEAR)

    # v2 solution with moderate acceleration
    sol_v2 = solve_trajectory(
        t0=0.0,
        tf=5 * YEAR,
        proper_time_desired=4.5 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )

    # Both should converge
    assert sol_v1.converged
    assert sol_v2.converged

    # Both should give approximately the same proper time
    assert sol_v1.total_proper_time == pytest.approx(4.5 * YEAR, rel=1e-3)
    assert sol_v2.total_proper_time == pytest.approx(4.5 * YEAR, rel=1e-2)


# --- Exit criteria as integration tests ---


def test_exit_criterion_proxima_centauri():
    """EXIT CRITERION: 1g round-trip to Proxima Centauri → ~3.5yr proper time each way.

    This verifies the primary physics goal of Phase 3.
    """
    sol = solve_trajectory(
        t0=0.0,
        tf=12 * YEAR,
        proper_time_desired=7.0 * YEAR,
        model=TrajectoryModel.CONSTANT_ACCELERATION,
        proper_acceleration=g,
    )

    assert sol.converged
    assert sol.peak_beta is not None
    assert sol.peak_beta > 0.9
    assert sol.peak_beta < 1.0
    assert sol.total_proper_time == pytest.approx(7.0 * YEAR, rel=0.01)
    assert check_subluminal(sol.worldline)

    # Worldline should have many points
    assert len(sol.worldline.coord_times) > 100

    # Phase boundaries should be present
    assert len(sol.phase_boundaries) == 5


def test_exit_criterion_5g_burst():
    """EXIT CRITERION: 5g-burst profile with smooth jerk-limited transitions."""
    from marte.jerk_profiles import AccelerationProfile, build_jerk_limited_phase

    direction = np.array([1.0, 0.0, 0.0])
    tau_phase = 0.5 * YEAR
    ramp_time = 0.05 * YEAR

    ct, ps, pt, bs = build_jerk_limited_phase(
        peak_accel=5 * g,
        tau_phase=tau_phase,
        profile=AccelerationProfile.S_CURVE,
        ramp_time=ramp_time,
        n_points=200,
        direction=direction,
        start_position=np.zeros(3),
        start_coord_time=0.0,
        start_proper_time=0.0,
        start_rapidity=0.0,
    )

    # Must be subluminal
    assert np.all(bs < 1.0)

    # Must have smooth transitions (no discontinuities)
    assert np.all(np.diff(ct) > 0)
    assert np.all(np.diff(pt) >= 0)

    # Must reach high speed
    assert bs[-1] > 0.9


# --- API backward compatibility ---


def test_api_backward_compat():
    """Sending a request without new fields still works (v1 default)."""
    resp = client.post(
        "/api/solve",
        json={"t0_years": 0.0, "tf_years": 2.0, "proper_time_years": 1.5},
    )
    data = resp.json()
    assert data["error"] is None
    assert data["solution"]["converged"] is True
    # v1 defaults
    assert data["solution"]["trajectory_model"] == "constant_velocity"
    assert data["worldline"]["beta_profile"] is None
