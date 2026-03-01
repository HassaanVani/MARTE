"""Schwarzschild metric corrections for GR proper time along SR worldlines.

GR corrections are computed as post-processing on existing SR trajectories.
The weak-field correction at 1 AU is ~10⁻⁸, far below solver tolerance,
so a full geodesic integrator is unnecessary.
"""

from dataclasses import dataclass, field
from math import sqrt

import numpy as np
from numpy.typing import NDArray

from marte.constants import (
    GM_SUN,
    SCHWARZSCHILD_RADIUS_SUN,
    SPEED_OF_LIGHT,
)
from marte.trajectory import Worldline

c = SPEED_OF_LIGHT
r_s = SCHWARZSCHILD_RADIUS_SUN


def schwarzschild_time_dilation_factor(r: float) -> float:
    """Gravitational time dilation factor at distance r from the Sun.

    Returns √(1 - r_s / r) where r_s is the Schwarzschild radius of the Sun.
    """
    return sqrt(1.0 - r_s / r)


def gravitational_potential_sun(r: float) -> float:
    """Newtonian gravitational potential at distance r from the Sun (J/kg).

    Returns -GM_Sun / r.
    """
    return -GM_SUN / r


def gr_proper_time_factor(r: float, beta: float) -> float:
    """Combined SR + GR proper time factor in Schwarzschild metric.

    Returns √(1 - r_s/r - β²) where β = v/c.

    In the weak-field slow-motion limit this reduces to:
    - √(1 - β²) when r → ∞ (pure SR)
    - √(1 - r_s/r) when β → 0 (pure gravitational dilation)
    """
    arg = 1.0 - r_s / r - beta**2
    if arg <= 0:
        return 0.0
    return sqrt(arg)


def sr_proper_time(worldline: Worldline) -> float:
    """Integrate SR proper time along a worldline: dτ = √(1 - β²) dt."""
    ct = worldline.coord_times
    pos = worldline.positions
    tau = 0.0

    for i in range(len(ct) - 1):
        dt = ct[i + 1] - ct[i]
        if dt <= 0:
            continue
        dr = np.linalg.norm(pos[i + 1] - pos[i])
        beta = dr / (c * dt)
        if beta >= 1.0:
            beta = 1.0 - 1e-15
        dtau = dt * sqrt(1.0 - beta**2)
        tau += dtau

    return tau


def gr_corrected_proper_time(worldline: Worldline) -> tuple[float, float, float, list[float]]:
    """Integrate GR-corrected proper time along a worldline.

    Uses the Schwarzschild metric: dτ² = (1 - r_s/r) dt² - dr²/c²

    Returns:
        (gr_tau, min_r, max_dilation, gr_factor_profile)
        - gr_tau: total GR proper time (s)
        - min_r: minimum distance from Sun along worldline (m)
        - max_dilation: maximum gravitational dilation factor encountered
        - gr_factor_profile: GR dτ/dt factor at each segment midpoint
    """
    ct = worldline.coord_times
    pos = worldline.positions
    tau = 0.0
    min_r = float("inf")
    max_dilation = 0.0
    gr_factor_profile = []

    for i in range(len(ct) - 1):
        dt = ct[i + 1] - ct[i]
        if dt <= 0:
            gr_factor_profile.append(1.0)
            continue

        dr = np.linalg.norm(pos[i + 1] - pos[i])
        beta = dr / (c * dt)
        if beta >= 1.0:
            beta = 1.0 - 1e-15

        # Distance from Sun at segment midpoint
        mid_pos = (pos[i] + pos[i + 1]) / 2.0
        r = float(np.linalg.norm(mid_pos))
        if r < 1.0:
            r = 1.0  # safety floor

        min_r = min(min_r, r)

        # Gravitational dilation at this point
        grav_dilation = r_s / r
        max_dilation = max(max_dilation, grav_dilation)

        # Combined factor: √(1 - r_s/r - β²)
        factor = gr_proper_time_factor(r, beta)
        gr_factor_profile.append(factor)
        tau += dt * factor

    return tau, min_r, max_dilation, gr_factor_profile


@dataclass
class GRDiagnostics:
    """Diagnostics from GR correction of an SR trajectory."""

    sr_proper_time_s: float
    gr_proper_time_s: float
    delta_tau_s: float               # gr - sr (negative = GR clocks slower)
    relative_correction: float       # |delta_tau| / sr_tau
    min_distance_from_sun_m: float
    max_gravitational_dilation: float
    gr_factor_profile: list[float] = field(default_factory=list)


def gr_correction(worldline: Worldline) -> GRDiagnostics:
    """Compute GR correction diagnostics for a worldline.

    Compares SR-only proper time with Schwarzschild-corrected proper time.
    """
    sr_tau = sr_proper_time(worldline)
    gr_tau, min_r, max_dilation, profile = gr_corrected_proper_time(worldline)
    delta = gr_tau - sr_tau
    relative = abs(delta) / sr_tau if sr_tau > 0 else 0.0

    return GRDiagnostics(
        sr_proper_time_s=sr_tau,
        gr_proper_time_s=gr_tau,
        delta_tau_s=delta,
        relative_correction=relative,
        min_distance_from_sun_m=min_r,
        max_gravitational_dilation=max_dilation,
        gr_factor_profile=profile,
    )
