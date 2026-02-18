"""Visualization functions for MARTE trajectory solutions."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from marte.constants import AU, EARTH_ORBITAL_RADIUS, SPEED_OF_LIGHT, YEAR
from marte.orbital import earth_position
from marte.solver import TrajectorySolution


def plot_orbital_view(solution: TrajectorySolution) -> Figure:
    """Plot a 2D orbital view of the trajectory in the ecliptic plane.

    Shows Earth's orbit, the ship trajectory (outbound + inbound legs),
    and markers at departure, turnaround, and arrival.

    Args:
        solution: A solved TrajectorySolution.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Earth orbit (full circle)
    theta = np.linspace(0, 2 * np.pi, 360)
    earth_x = EARTH_ORBITAL_RADIUS * np.cos(theta) / AU
    earth_y = EARTH_ORBITAL_RADIUS * np.sin(theta) / AU
    ax.plot(earth_x, earth_y, "b--", alpha=0.3, label="Earth orbit")

    # Earth positions along the trajectory timespan
    wl = solution.worldline
    t0 = wl.coord_times[0]
    tf = wl.coord_times[-1]
    t_samples = np.linspace(t0, tf, 100)
    earth_traj = np.array([earth_position(t) for t in t_samples])
    ax.plot(
        earth_traj[:, 0] / AU, earth_traj[:, 1] / AU,
        "b-", linewidth=1.5, label="Earth path",
    )

    # Ship trajectory
    ship_x = wl.positions[:, 0] / AU
    ship_y = wl.positions[:, 1] / AU
    ax.plot(ship_x, ship_y, "r-", linewidth=2, label="Ship trajectory")

    # Markers: dynamic indexing for variable-length worldlines
    mid_idx = len(ship_x) // 2
    ax.plot(ship_x[0], ship_y[0], "go", markersize=10, label="Departure")
    ax.plot(ship_x[mid_idx], ship_y[mid_idx], "rs", markersize=10, label="Turnaround")
    ax.plot(ship_x[-1], ship_y[-1], "b^", markersize=10, label="Arrival")

    # Sun at origin
    ax.plot(0, 0, "yo", markersize=15, label="Sun")

    ax.set_xlabel("x (AU)")
    ax.set_ylabel("y (AU)")
    ax.set_title("Orbital View — Ship Trajectory")
    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_minkowski_diagram(solution: TrajectorySolution) -> Figure:
    """Plot a Minkowski spacetime diagram of the trajectory.

    Vertical axis: coordinate time. Horizontal axis: spatial displacement
    along the trajectory direction from the departure point.

    Shows the Earth worldline, ship worldline, and light cones at departure.

    Args:
        solution: A solved TrajectorySolution.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    wl = solution.worldline
    t0 = wl.coord_times[0]
    tf = wl.coord_times[-1]
    r_depart = wl.positions[0]

    # Ship worldline: signed displacement projected along outbound direction
    dir_out = solution.direction_out
    ship_signed = np.array([
        np.dot(wl.positions[i] - r_depart, dir_out)
        for i in range(len(wl.coord_times))
    ])

    ship_t = (wl.coord_times - t0) / YEAR
    ship_x = ship_signed / AU

    ax.plot(ship_x, ship_t, "r-", linewidth=2, label="Ship worldline")

    # Earth worldline
    t_samples = np.linspace(t0, tf, 200)
    earth_positions = np.array([earth_position(t) for t in t_samples])
    earth_signed = np.array([
        np.dot(earth_positions[i] - r_depart, dir_out)
        for i in range(len(t_samples))
    ])
    ax.plot(
        earth_signed / AU, (t_samples - t0) / YEAR,
        "b-", linewidth=1.5, label="Earth worldline",
    )

    # Light cones at departure
    t_range = (tf - t0) / YEAR
    c_au_per_year = SPEED_OF_LIGHT * YEAR / AU
    lc_t = np.array([0, t_range])
    ax.plot(lc_t * c_au_per_year, lc_t, "y--", alpha=0.5, linewidth=1)
    ax.plot(
        -lc_t * c_au_per_year, lc_t,
        "y--", alpha=0.5, linewidth=1, label="Light cone",
    )

    # Proper time ticks on ship worldline
    for i in range(len(wl.coord_times)):
        ax.plot(ship_x[i], ship_t[i], "ro", markersize=6)
        ax.annotate(
            f"  τ={wl.proper_times[i] / YEAR:.2f}y",
            (ship_x[i], ship_t[i]),
            fontsize=8,
        )

    ax.set_xlabel("Displacement along trajectory (AU)")
    ax.set_ylabel("Coordinate time (years)")
    ax.set_title("Minkowski Diagram")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_proper_time_curve(solution: TrajectorySolution) -> Figure:
    """Plot proper time τ as a function of coordinate time t.

    Shows how the onboard clock runs slower than coordinate time,
    with slope changes at turnaround.

    Args:
        solution: A solved TrajectorySolution.

    Returns:
        A matplotlib Figure.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    wl = solution.worldline
    t0 = wl.coord_times[0]

    coord_t = (wl.coord_times - t0) / YEAR
    proper_t = wl.proper_times / YEAR

    # Ship proper time (piecewise linear for constant velocity legs)
    ax.plot(
        coord_t, proper_t, "r-o",
        linewidth=2, markersize=8, label="Ship proper time τ(t)",
    )

    # Reference: τ = t line (no time dilation)
    t_range = np.array([0, coord_t[-1]])
    ax.plot(t_range, t_range, "k--", alpha=0.4, label="τ = t (no dilation)")

    ax.set_xlabel("Coordinate time (years)")
    ax.set_ylabel("Proper time (years)")
    ax.set_title("Proper Time vs Coordinate Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
