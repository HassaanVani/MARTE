"""Tests for marte.trajectory — ship worldline computation."""

import numpy as np
import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_worldline_has_correct_departure_time():
    from marte.trajectory import compute_ship_worldline

    wl = compute_ship_worldline(
        departure_time=0.0,
        turnaround_time=5e6,
        arrival_time=1e7,
        velocity_out=np.array([1e8, 0.0, 0.0]),
        velocity_in=np.array([-1e8, 0.0, 0.0]),
    )
    assert wl.coord_times[0] == pytest.approx(0.0)


@pytest.mark.skip(reason="not yet implemented")
def test_worldline_has_correct_arrival_time():
    from marte.trajectory import compute_ship_worldline

    wl = compute_ship_worldline(
        departure_time=0.0,
        turnaround_time=5e6,
        arrival_time=1e7,
        velocity_out=np.array([1e8, 0.0, 0.0]),
        velocity_in=np.array([-1e8, 0.0, 0.0]),
    )
    assert wl.coord_times[-1] == pytest.approx(1e7)


@pytest.mark.skip(reason="not yet implemented")
def test_worldline_proper_time_monotonic():
    from marte.trajectory import compute_ship_worldline

    wl = compute_ship_worldline(
        departure_time=0.0,
        turnaround_time=5e6,
        arrival_time=1e7,
        velocity_out=np.array([1e8, 0.0, 0.0]),
        velocity_in=np.array([-1e8, 0.0, 0.0]),
    )
    diffs = np.diff(wl.proper_times)
    assert np.all(diffs >= 0)


@pytest.mark.skip(reason="not yet implemented")
def test_worldline_proper_time_less_than_coord_time():
    from marte.trajectory import compute_ship_worldline

    wl = compute_ship_worldline(
        departure_time=0.0,
        turnaround_time=5e6,
        arrival_time=1e7,
        velocity_out=np.array([1e8, 0.0, 0.0]),
        velocity_in=np.array([-1e8, 0.0, 0.0]),
    )
    total_proper = wl.proper_times[-1]
    total_coord = wl.coord_times[-1] - wl.coord_times[0]
    assert total_proper < total_coord
