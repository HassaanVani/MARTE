"""Tests for marte.spacetime — Minkowski interval and causal structure."""

import numpy as np
import pytest

from marte.constants import SPEED_OF_LIGHT


def test_minkowski_interval_same_event():
    from marte.spacetime import minkowski_interval

    event = np.array([0.0, 0.0, 0.0, 0.0])
    assert minkowski_interval(event, event) == pytest.approx(0.0)


def test_minkowski_interval_timelike():
    from marte.spacetime import is_timelike, minkowski_interval

    # Two events: same place, 1 second apart → purely timelike
    e1 = np.array([0.0, 0.0, 0.0, 0.0])
    e2 = np.array([1.0, 0.0, 0.0, 0.0])
    interval = minkowski_interval(e1, e2)
    assert interval < 0  # timelike: ds² < 0
    assert is_timelike(interval)


def test_minkowski_interval_spacelike():
    from marte.spacetime import is_timelike, minkowski_interval

    # Two events: same time, 1 meter apart → spacelike
    e1 = np.array([0.0, 0.0, 0.0, 0.0])
    e2 = np.array([0.0, 1.0, 0.0, 0.0])
    interval = minkowski_interval(e1, e2)
    assert interval > 0  # spacelike: ds² > 0
    assert not is_timelike(interval)


def test_minkowski_interval_null():
    from marte.spacetime import minkowski_interval

    # Light ray: travels c meters in 1 second
    e1 = np.array([0.0, 0.0, 0.0, 0.0])
    e2 = np.array([1.0, SPEED_OF_LIGHT, 0.0, 0.0])
    interval = minkowski_interval(e1, e2)
    assert interval == pytest.approx(0.0, abs=1e-6)
