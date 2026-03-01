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

# --- General Relativity & Planetary Constants ---

# Gravitational constant (m³ kg⁻¹ s⁻²)
GRAVITATIONAL_CONSTANT = 6.67430e-11

# Solar mass (kg)
M_SUN = 1.98892e30

# Solar gravitational parameter (m³/s²) — IAU 2015
GM_SUN = 1.32712440018e20

# Schwarzschild radius of the Sun (m): r_s = 2GM/c²
SCHWARZSCHILD_RADIUS_SUN = 2 * GM_SUN / SPEED_OF_LIGHT**2

# Mercury
MERCURY_ORBITAL_RADIUS = 5.791e10                          # m (0.387 AU)
MERCURY_ORBITAL_ANGULAR_VEL = 2 * pi / (0.2408467 * YEAR)  # rad/s
M_MERCURY = 3.3011e23                                      # kg

# Venus
VENUS_ORBITAL_RADIUS = 1.0821e11                           # m (0.723 AU)
VENUS_ORBITAL_ANGULAR_VEL = 2 * pi / (0.61519726 * YEAR)   # rad/s
M_VENUS = 4.8675e24                                        # kg

# Mars
MARS_ORBITAL_RADIUS = 2.2794e11                            # m (1.524 AU)
MARS_ORBITAL_ANGULAR_VEL = 2 * pi / (1.8808476 * YEAR)     # rad/s
M_MARS = 6.4171e23                                         # kg

# Jupiter
M_JUPITER = 1.89813e27                                  # kg
JUPITER_ORBITAL_RADIUS = 7.785e11                        # m (5.2 AU)
JUPITER_ORBITAL_ANGULAR_VEL = 2 * pi / (11.862 * YEAR)  # rad/s

# Saturn
M_SATURN = 5.6834e26                                     # kg
SATURN_ORBITAL_RADIUS = 1.4335e12                         # m (9.58 AU)
SATURN_ORBITAL_ANGULAR_VEL = 2 * pi / (29.4571 * YEAR)   # rad/s

# J2000.0 epoch as Julian Date
J2000_JD = 2451545.0
