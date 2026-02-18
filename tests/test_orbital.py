"""Tests for marte.orbital — Earth position and velocity models."""

import numpy as np
import pytest


def test_earth_position_at_t_zero():
    from marte.constants import EARTH_ORBITAL_RADIUS
    from marte.orbital import earth_position

    pos = earth_position(0.0)
    assert pos.shape == (3,)
    assert pos[0] == pytest.approx(EARTH_ORBITAL_RADIUS)
    assert pos[1] == pytest.approx(0.0)
    assert pos[2] == pytest.approx(0.0)


def test_earth_position_quarter_orbit():
    from marte.constants import EARTH_ORBITAL_RADIUS, YEAR
    from marte.orbital import earth_position

    pos = earth_position(YEAR / 4)
    assert pos[0] == pytest.approx(0.0, abs=1e3)
    assert pos[1] == pytest.approx(EARTH_ORBITAL_RADIUS, rel=1e-6)


def test_earth_position_is_on_orbital_radius():
    from marte.constants import EARTH_ORBITAL_RADIUS, YEAR
    from marte.orbital import earth_position

    for t in [0.0, YEAR / 6, YEAR / 3, YEAR / 2, YEAR]:
        pos = earth_position(t)
        r = np.linalg.norm(pos)
        assert r == pytest.approx(EARTH_ORBITAL_RADIUS, rel=1e-9)


def test_earth_velocity_perpendicular_to_position():
    from marte.constants import YEAR
    from marte.orbital import earth_position, earth_velocity

    for t in [0.0, YEAR / 4, YEAR / 2]:
        pos = earth_position(t)
        vel = earth_velocity(t)
        dot = np.dot(pos, vel)
        assert dot == pytest.approx(0.0, abs=1e-3)


def test_earth_velocity_magnitude():
    from marte.constants import EARTH_ORBITAL_ANGULAR_VEL, EARTH_ORBITAL_RADIUS
    from marte.orbital import earth_velocity

    vel = earth_velocity(0.0)
    expected_speed = EARTH_ORBITAL_RADIUS * EARTH_ORBITAL_ANGULAR_VEL
    assert np.linalg.norm(vel) == pytest.approx(expected_speed, rel=1e-9)
