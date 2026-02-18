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
