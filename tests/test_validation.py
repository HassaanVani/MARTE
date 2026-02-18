"""Tests for marte.validation — physics consistency checks."""

import numpy as np
import pytest

from marte.trajectory import Worldline


@pytest.mark.skip(reason="not yet implemented")
def test_check_subluminal_valid():
    from marte.validation import check_subluminal

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 9e6]),
    )
    assert check_subluminal(wl)


@pytest.mark.skip(reason="not yet implemented")
def test_check_proper_time_consistency_pass():
    from marte.validation import check_proper_time_consistency

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert check_proper_time_consistency(wl, expected_tau=8e6)


@pytest.mark.skip(reason="not yet implemented")
def test_check_proper_time_consistency_fail():
    from marte.validation import check_proper_time_consistency

    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e15, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert not check_proper_time_consistency(wl, expected_tau=5e6)


@pytest.mark.skip(reason="not yet implemented")
def test_check_arrival_intersection_pass():
    from marte.validation import check_arrival_intersection

    earth_pos = np.array([1e11, 0.0, 0.0])
    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [1e11, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert check_arrival_intersection(wl, earth_pos)


@pytest.mark.skip(reason="not yet implemented")
def test_check_arrival_intersection_fail():
    from marte.validation import check_arrival_intersection

    earth_pos = np.array([1e11, 0.0, 0.0])
    wl = Worldline(
        coord_times=np.array([0.0, 1e7]),
        positions=np.array([[0.0, 0.0, 0.0], [5e10, 0.0, 0.0]]),
        proper_times=np.array([0.0, 8e6]),
    )
    assert not check_arrival_intersection(wl, earth_pos)
