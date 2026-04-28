"""Tests for marte.validation — physics consistency checks."""

import numpy as np

from marte.trajectory import Worldline


def test_check_subluminal_valid():
    from marte.validation import check_subluminal

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 9e6]),
    )
    assert check_subluminal(wl)


def test_check_proper_time_consistency_pass():
    from marte.validation import check_proper_time_consistency

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert check_proper_time_consistency(wl, expected_tau=8e6)


def test_check_proper_time_consistency_fail():
    from marte.validation import check_proper_time_consistency

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert not check_proper_time_consistency(wl, expected_tau=5e6)


def test_check_arrival_intersection_pass():
    from marte.validation import check_arrival_intersection

    earth_pos = np.array([1e11, 0.0, 0.0])
    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e11, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert check_arrival_intersection(wl, earth_pos)
def test_check_arrival_intersection_fail():
    from marte.validation import check_arrival_intersection

    earth_pos = np.array([1e11, 0.0, 0.0])
    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [5e10, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert not check_arrival_intersection(wl, earth_pos)


def test_ephemeris_elliptical_bounds():
    """Verify that the elliptical Earth model stays within reasonable bounds of JPL Horizons."""
    from marte.ephemeris import _get_client
    from marte.orbital import earth_position
    from marte.constants import YEAR, AU
    
    # We test a 1-year window
    t_end = 1.0 * YEAR
    times = np.linspace(0.0, t_end, 12)
    
    # Fetch Horizons data (using 30-day step to minimize requests during test)
    client = _get_client()
    earth_horiz = client.fetch_body_ephemeris("399", 0.0, t_end, step_days=30)
    
    errors = []
    for t in times:
        pos_horiz = earth_horiz.position(t)
        pos_ellip = earth_position(t, elliptical=True)
        errors.append(np.linalg.norm(pos_horiz - pos_ellip) / AU)
        
    # Elliptical model should stay within ~0.06 AU of the real perturbed Earth
    assert max(errors) < 0.1, f"Elliptical model deviates too much from Horizons: {max(errors)} AU"

