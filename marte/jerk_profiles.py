"""Jerk-limited acceleration profiles for smooth thrust transitions.

Replaces step-function acceleration changes at phase boundaries with
smooth ramp-up/ramp-down profiles. Three profile types:
  - STEP: Instantaneous transition (matches Phase 3a results)
  - LINEAR_RAMP: Linear ramp from 0 to peak and back
  - S_CURVE: Sinusoidal (half-cosine) ramp for smooth jerk

The acceleration schedule a(τ) is integrated numerically to produce
rapidity, coordinate time, and position.
"""

from dataclasses import dataclass
from enum import Enum
from math import cos, pi

import numpy as np
from numpy.typing import NDArray

from marte.constants import SPEED_OF_LIGHT

c = SPEED_OF_LIGHT


class AccelerationProfile(Enum):
    """Acceleration transition profile type."""

    STEP = "step"
    LINEAR_RAMP = "linear_ramp"
    S_CURVE = "s_curve"


@dataclass
class GToleranceProfile:
    """Human g-tolerance constraints.

    Attributes:
        max_sustained_g: Maximum sustained acceleration (g).
        max_peak_g: Maximum peak acceleration (g).
        max_peak_duration_s: Maximum duration at peak acceleration (s).
        ramp_time_s: Time to ramp up/down (s).
    """

    max_sustained_g: float
    max_peak_g: float
    max_peak_duration_s: float
    ramp_time_s: float


def acceleration_schedule(
    tau_phase: float,
    peak_accel: float,
    profile: AccelerationProfile,
    ramp_time: float,
    n_points: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate an acceleration schedule a(τ) for one phase.

    Args:
        tau_phase: Total proper time duration of the phase (s).
        peak_accel: Peak proper acceleration (m/s²).
        profile: Acceleration profile type.
        ramp_time: Ramp-up/ramp-down time (s). Clamped to tau_phase/2.
        n_points: Number of sample points.

    Returns:
        (tau_points, accel_points): Proper time and acceleration arrays.
    """
    tau_points = np.linspace(0.0, tau_phase, n_points)
    accel_points = np.empty(n_points)

    ramp_time = min(ramp_time, tau_phase / 2.0)

    if profile == AccelerationProfile.STEP:
        accel_points[:] = peak_accel
    elif profile == AccelerationProfile.LINEAR_RAMP:
        for i, tau in enumerate(tau_points):
            if tau < ramp_time:
                accel_points[i] = peak_accel * (tau / ramp_time)
            elif tau > tau_phase - ramp_time:
                accel_points[i] = peak_accel * ((tau_phase - tau) / ramp_time)
            else:
                accel_points[i] = peak_accel
    elif profile == AccelerationProfile.S_CURVE:
        for i, tau in enumerate(tau_points):
            if tau < ramp_time:
                # Half-cosine ramp up: a = peak * (1 - cos(π τ / ramp)) / 2
                accel_points[i] = peak_accel * (1.0 - cos(pi * tau / ramp_time)) / 2.0
            elif tau > tau_phase - ramp_time:
                # Half-cosine ramp down
                t_from_end = tau_phase - tau
                accel_points[i] = peak_accel * (1.0 - cos(pi * t_from_end / ramp_time)) / 2.0
            else:
                accel_points[i] = peak_accel
    else:
        raise ValueError(f"Unknown profile: {profile}")

    return tau_points, accel_points


def build_jerk_limited_phase(
    peak_accel: float,
    tau_phase: float,
    profile: AccelerationProfile,
    ramp_time: float,
    n_points: int,
    direction: NDArray[np.float64],
    start_position: NDArray[np.float64],
    start_coord_time: float,
    start_proper_time: float,
    start_rapidity: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Build one phase with variable acceleration via numerical integration.

    Integrates the acceleration schedule using the trapezoidal rule on rapidity:
        dφ/dτ = a(τ)/c
        dt/dτ = cosh(φ)
        dx/dτ = c sinh(φ)

    Args:
        peak_accel: Peak proper acceleration (m/s²), signed.
        tau_phase: Proper time duration (s).
        profile: Acceleration profile type.
        ramp_time: Ramp time (s).
        n_points: Sample points.
        direction: Unit direction vector, shape (3,).
        start_position: Starting position (m), shape (3,).
        start_coord_time: Starting coordinate time (s).
        start_proper_time: Starting proper time (s).
        start_rapidity: Starting rapidity.

    Returns:
        (coord_times, positions, proper_times, betas) arrays.
    """
    direction = np.asarray(direction, dtype=np.float64)
    start_position = np.asarray(start_position, dtype=np.float64)

    sign = 1.0 if peak_accel >= 0 else -1.0
    tau_points, accel_points = acceleration_schedule(
        tau_phase, abs(peak_accel), profile, ramp_time, n_points
    )
    # Apply sign
    accel_points = sign * accel_points

    coord_times = np.empty(n_points)
    positions = np.empty((n_points, 3))
    proper_times = np.empty(n_points)
    betas = np.empty(n_points)

    phi = start_rapidity
    t_coord = start_coord_time
    x_disp = 0.0  # displacement along direction

    coord_times[0] = t_coord
    positions[0] = start_position.copy()
    proper_times[0] = start_proper_time
    betas[0] = abs(np.tanh(phi))

    for i in range(1, n_points):
        dtau = tau_points[i] - tau_points[i - 1]

        # Trapezoidal rule for rapidity: dφ = a(τ)/c dτ
        a_avg = (accel_points[i - 1] + accel_points[i]) / 2.0
        dphi = a_avg * dtau / c
        phi_mid = phi + dphi / 2.0

        # Integration for t and x using midpoint rapidity
        dt = np.cosh(phi_mid) * dtau
        dx = c * np.sinh(phi_mid) * dtau

        phi += dphi
        t_coord += dt
        x_disp += dx

        coord_times[i] = t_coord
        positions[i] = start_position + direction * x_disp
        proper_times[i] = start_proper_time + tau_points[i]
        betas[i] = abs(np.tanh(phi))

    return coord_times, positions, proper_times, betas
