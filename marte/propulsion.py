"""Propulsion and fuel budget analysis for relativistic trajectories.

Post-solver module: computes mass ratios and fuel budgets from a solved
trajectory's total rapidity change, using the relativistic Tsiolkovsky
rocket equation.

Reference: Forward, R.L., "A Transparent Derivation of the Relativistic
Rocket Equation" (1995).
"""

from dataclasses import dataclass
from math import atanh, exp

from marte.constants import SPEED_OF_LIGHT

c = SPEED_OF_LIGHT


@dataclass
class FuelBudget:
    """Fuel budget analysis for a trajectory.

    Attributes:
        exhaust_velocity: Exhaust velocity v_e (m/s).
        mass_ratio: Initial-to-final mass ratio m0/mf.
        fuel_mass_fraction: Fraction of initial mass that is fuel (1 - 1/mass_ratio).
        fuel_mass_kg: Fuel mass (kg) for the given dry mass.
        total_delta_v: Total rapidity change (dimensionless).
        total_energy_joules: Minimum energy required (J).
    """

    exhaust_velocity: float
    mass_ratio: float
    fuel_mass_fraction: float
    fuel_mass_kg: float
    total_delta_v: float
    total_energy_joules: float


def relativistic_tsiolkovsky(delta_rapidity: float, exhaust_velocity: float) -> float:
    """Compute the mass ratio from the relativistic Tsiolkovsky equation.

    For a rocket with exhaust velocity v_e, the mass ratio to achieve
    a total rapidity change Δφ is:

        m0/mf = exp(Δφ / arctanh(v_e/c))

    In the classical limit (v_e << c), arctanh(v_e/c) ≈ v_e/c, and this
    reduces to: m0/mf = exp(Δv / v_e) (classical Tsiolkovsky).

    Args:
        delta_rapidity: Total rapidity change Δφ (dimensionless). Sum of all
            phase rapidity changes (always positive).
        exhaust_velocity: Rocket exhaust velocity v_e (m/s). Must be < c.

    Returns:
        Mass ratio m0/mf (dimensionless, >= 1).
    """
    if exhaust_velocity <= 0:
        raise ValueError("Exhaust velocity must be positive.")
    if exhaust_velocity >= c:
        raise ValueError("Exhaust velocity must be less than c.")

    beta_e = exhaust_velocity / c
    phi_e = atanh(beta_e)

    return exp(delta_rapidity / phi_e)


def compute_fuel_budget(
    total_rapidity_change: float,
    exhaust_velocity: float,
    dry_mass: float,
) -> FuelBudget:
    """Compute the complete fuel budget for a trajectory.

    Args:
        total_rapidity_change: Sum of absolute rapidity changes across all phases.
        exhaust_velocity: Rocket exhaust velocity v_e (m/s).
        dry_mass: Payload + structure mass without fuel (kg).

    Returns:
        A FuelBudget dataclass with all computed quantities.
    """
    mass_ratio = relativistic_tsiolkovsky(total_rapidity_change, exhaust_velocity)
    fuel_mass_fraction = 1.0 - 1.0 / mass_ratio
    fuel_mass = dry_mass * (mass_ratio - 1.0)

    # Minimum energy: rest mass energy of consumed fuel
    # E = (m0 - mf) * c^2 = fuel_mass * c^2
    # More precisely, for a photon rocket: E = mf * c^2 * (mass_ratio - 1)
    total_energy = fuel_mass * c**2

    return FuelBudget(
        exhaust_velocity=exhaust_velocity,
        mass_ratio=mass_ratio,
        fuel_mass_fraction=fuel_mass_fraction,
        fuel_mass_kg=fuel_mass,
        total_delta_v=total_rapidity_change,
        total_energy_joules=total_energy,
    )
