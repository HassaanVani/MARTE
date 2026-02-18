"""Physical constants in SI units for the MARTE physics engine."""

from math import pi

# Speed of light (m/s)
SPEED_OF_LIGHT = 299_792_458

# Astronomical unit (m)
AU = 1.496e11

# Julian year (s)
YEAR = 365.25 * 24 * 3600

# Earth orbital radius — circular approximation (m)
EARTH_ORBITAL_RADIUS = AU

# Earth orbital angular velocity (rad/s)
EARTH_ORBITAL_ANGULAR_VEL = 2 * pi / YEAR

# Standard gravity (m/s²) — ISO 80000-3
STANDARD_GRAVITY = 9.80665

# Earth orbital eccentricity
EARTH_ECCENTRICITY = 0.0167086

# Earth longitude of perihelion (radians from vernal equinox)
# J2000 value ≈ 102.9° = 1.796 rad
EARTH_PERIHELION_LONGITUDE = 1.796
