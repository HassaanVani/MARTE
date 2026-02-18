"""Tests for marte.constants — verify physical constant values."""

import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_speed_of_light():
    from marte.constants import SPEED_OF_LIGHT

    assert SPEED_OF_LIGHT == 299_792_458


@pytest.mark.skip(reason="not yet implemented")
def test_au():
    from marte.constants import AU

    assert AU == pytest.approx(1.496e11)


@pytest.mark.skip(reason="not yet implemented")
def test_year_seconds():
    from marte.constants import YEAR

    assert YEAR == pytest.approx(365.25 * 24 * 3600)


@pytest.mark.skip(reason="not yet implemented")
def test_earth_orbital_radius():
    from marte.constants import AU, EARTH_ORBITAL_RADIUS

    assert EARTH_ORBITAL_RADIUS == AU


@pytest.mark.skip(reason="not yet implemented")
def test_earth_orbital_angular_vel():
    import math

    from marte.constants import EARTH_ORBITAL_ANGULAR_VEL, YEAR

    assert EARTH_ORBITAL_ANGULAR_VEL == pytest.approx(2 * math.pi / YEAR)
