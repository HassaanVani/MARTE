"""Tests for marte.propulsion — fuel budget and relativistic Tsiolkovsky equation."""

import pytest

from marte.constants import SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.propulsion import compute_fuel_budget, relativistic_tsiolkovsky

c = SPEED_OF_LIGHT
g = STANDARD_GRAVITY


def test_mass_ratio_always_greater_than_one():
    """Mass ratio m0/mf >= 1 for any positive delta-v."""
    for delta_phi in [0.01, 0.1, 1.0, 5.0, 10.0]:
        mr = relativistic_tsiolkovsky(delta_phi, 0.1 * c)
        assert mr >= 1.0


def test_mass_ratio_increases_with_delta_rapidity():
    """Higher delta-rapidity → higher mass ratio."""
    mr_small = relativistic_tsiolkovsky(1.0, 0.1 * c)
    mr_large = relativistic_tsiolkovsky(5.0, 0.1 * c)
    assert mr_large > mr_small


def test_mass_ratio_decreases_with_exhaust_velocity():
    """Higher exhaust velocity → lower mass ratio for same delta-v."""
    mr_slow = relativistic_tsiolkovsky(2.0, 0.01 * c)
    mr_fast = relativistic_tsiolkovsky(2.0, 0.1 * c)
    assert mr_slow > mr_fast


def test_classical_limit():
    """At low exhaust velocity, approaches classical Tsiolkovsky.

    Classical: m0/mf = exp(Δv / v_e)
    Relativistic: m0/mf = exp(Δφ / arctanh(v_e/c))

    For v_e << c: arctanh(v_e/c) ≈ v_e/c, and Δφ ≈ Δv/c
    So relativistic ≈ exp((Δv/c) / (v_e/c)) = exp(Δv/v_e) = classical
    """
    import math

    v_e = 4500.0  # Chemical rocket exhaust velocity (m/s)
    delta_v = 10000.0  # 10 km/s delta-v
    delta_rapidity = delta_v / c  # For v << c, rapidity ≈ v/c

    mr_rel = relativistic_tsiolkovsky(delta_rapidity, v_e)
    mr_classical = math.exp(delta_v / v_e)

    assert mr_rel == pytest.approx(mr_classical, rel=1e-6)


def test_zero_delta_rapidity():
    """Zero rapidity change → mass ratio = 1."""
    mr = relativistic_tsiolkovsky(0.0, 0.1 * c)
    assert mr == pytest.approx(1.0)


def test_rejects_superluminal_exhaust():
    """Exhaust velocity >= c is rejected."""
    with pytest.raises(ValueError):
        relativistic_tsiolkovsky(1.0, c)
    with pytest.raises(ValueError):
        relativistic_tsiolkovsky(1.0, 1.1 * c)


def test_rejects_negative_exhaust():
    """Negative exhaust velocity is rejected."""
    with pytest.raises(ValueError):
        relativistic_tsiolkovsky(1.0, -1000.0)


def test_fuel_budget_fields():
    """FuelBudget has all expected fields."""
    budget = compute_fuel_budget(
        total_rapidity_change=2.0,
        exhaust_velocity=0.1 * c,
        dry_mass=1000.0,
    )
    assert budget.exhaust_velocity == 0.1 * c
    assert budget.mass_ratio > 1.0
    assert 0.0 < budget.fuel_mass_fraction < 1.0
    assert budget.fuel_mass_kg > 0.0
    assert budget.total_delta_v == 2.0
    assert budget.total_energy_joules > 0.0


def test_fuel_mass_fraction_consistency():
    """fuel_mass_fraction = 1 - 1/mass_ratio."""
    budget = compute_fuel_budget(
        total_rapidity_change=3.0,
        exhaust_velocity=0.05 * c,
        dry_mass=500.0,
    )
    assert budget.fuel_mass_fraction == pytest.approx(1.0 - 1.0 / budget.mass_ratio)


def test_fuel_mass_consistency():
    """fuel_mass = dry_mass * (mass_ratio - 1)."""
    budget = compute_fuel_budget(
        total_rapidity_change=1.5,
        exhaust_velocity=0.2 * c,
        dry_mass=2000.0,
    )
    assert budget.fuel_mass_kg == pytest.approx(2000.0 * (budget.mass_ratio - 1.0))


def test_proxima_centauri_1g_fuel_budget():
    """1g Proxima Centauri round trip fuel budget is enormous.

    A 1g brachistochrone round trip to Proxima (4.24 ly) requires total
    rapidity change of about 4 × (g × τ_half / c) where τ_half ≈ 1.77yr.

    With a photon drive (v_e ≈ c), mass ratio ~ 60-80.
    With fusion drive (v_e ≈ 0.1c), mass ratio is astronomical.
    """
    # Total rapidity change: 4 phases, each with rapidity g*τ_half/c
    # τ_half ≈ 1.77yr for one-way brachistochrone
    tau_half = 1.77 * YEAR
    rapidity_per_phase = g * tau_half / c
    total_rapidity = 4 * rapidity_per_phase

    # Photon drive: v_e ≈ 0.999c (idealized)
    budget_photon = compute_fuel_budget(total_rapidity, 0.999 * c, 1000.0)
    assert budget_photon.mass_ratio > 1.0
    assert budget_photon.fuel_mass_kg > 0.0

    # Fusion drive: v_e ≈ 0.1c
    budget_fusion = compute_fuel_budget(total_rapidity, 0.1 * c, 1000.0)
    # Fusion mass ratio should be much higher than photon
    assert budget_fusion.mass_ratio > budget_photon.mass_ratio
