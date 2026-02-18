"""CLI entry point for MARTE trajectory computation (Phase 1 deliverable)."""

import argparse
import sys

import numpy as np

from marte.constants import SPEED_OF_LIGHT, YEAR
from marte.relativity import lorentz_factor
from marte.solver import solve_trajectory


def parse_time(value: str) -> float:
    """Parse a time value with optional unit suffix.

    Supports:
        '2y' or '2Y' → 2 Julian years in seconds
        '1.5y' → 1.5 Julian years in seconds
        '3.15e7' → raw seconds
        '0' → 0.0

    Args:
        value: Time string to parse.

    Returns:
        Time in seconds.
    """
    value = value.strip()
    if value.lower().endswith("y"):
        return float(value[:-1]) * YEAR
    return float(value)


def main() -> None:
    """Compute a relativistic trajectory from user-specified parameters."""
    parser = argparse.ArgumentParser(
        description="MARTE — Compute a relativistic round-trip trajectory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Time values accept 'y' suffix for Julian years (e.g., '2y' = 2 years).\n"
            "Without suffix, values are interpreted as seconds.\n\n"
            "Example:\n"
            "  uv run python scripts/compute_trajectory.py --t0 0 --tf 2y --tau 1.5y\n"
        ),
    )
    parser.add_argument("--t0", type=str, default="0", help="Departure time (default: 0)")
    parser.add_argument("--tf", type=str, required=True, help="Arrival time")
    parser.add_argument("--tau", type=str, required=True, help="Desired proper time")
    parser.add_argument("--mass", type=float, default=1000.0, help="Ship mass in kg (default: 1000)")
    parser.add_argument("--plot", action="store_true", help="Show matplotlib plots")

    args = parser.parse_args()

    t0 = parse_time(args.t0)
    tf = parse_time(args.tf)
    tau = parse_time(args.tau)

    print("=" * 60)
    print("MARTE — Relativistic Trajectory Solver")
    print("=" * 60)
    print(f"  Departure time (t0):  {t0:.6e} s  ({t0 / YEAR:.4f} years)")
    print(f"  Arrival time (tf):    {tf:.6e} s  ({tf / YEAR:.4f} years)")
    print(f"  Desired proper time:  {tau:.6e} s  ({tau / YEAR:.4f} years)")
    print(f"  Ship mass:            {args.mass:.1f} kg")
    print()

    try:
        solution = solve_trajectory(t0, tf, tau, mass=args.mass)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    beta = solution.velocity_magnitude
    gamma = lorentz_factor(beta)
    arrival_rel_speed = float(np.linalg.norm(solution.arrival_relative_velocity))

    print("--- Results ---")
    print(f"  beta (v/c):           {beta:.10f}")
    print(f"  gamma (Lorentz):      {gamma:.10f}")
    print(f"  Speed:                {beta * SPEED_OF_LIGHT:.3e} m/s")
    print(f"  Turnaround time:      {solution.turnaround_time:.6e} s  "
          f"({solution.turnaround_time / YEAR:.4f} years)")
    print(f"  Total proper time:    {solution.total_proper_time:.6e} s  "
          f"({solution.total_proper_time / YEAR:.4f} years)")
    print(f"  Kinetic energy:       {solution.energy:.6e} J")
    print(f"  Converged:            {solution.converged}")
    print(f"  Residual:             {solution.residual:.6e}")
    print()
    print("--- Directions ---")
    print(f"  Outbound direction:   {solution.direction_out}")
    print(f"  Inbound direction:    {solution.direction_in}")
    print()
    print("--- Rendezvous ---")
    print(f"  Arrival velocity (Earth frame): {solution.arrival_relative_velocity}")
    print(f"  Arrival speed (Earth frame):    {arrival_rel_speed:.3e} m/s  "
          f"({arrival_rel_speed / SPEED_OF_LIGHT:.6f} c)")
    print()
    print("--- Validation ---")
    print(f"  Subluminal (beta < 1):  {beta < 1.0}")
    print(f"  Proper time match:      tau_computed={solution.total_proper_time / YEAR:.6f}y  "
          f"vs  tau_desired={tau / YEAR:.6f}y")

    if args.plot:
        from marte.plotting import (
            plot_minkowski_diagram,
            plot_orbital_view,
            plot_proper_time_curve,
        )

        print("\nGenerating plots...")
        plot_orbital_view(solution)
        plot_minkowski_diagram(solution)
        plot_proper_time_curve(solution)

        import matplotlib.pyplot as plt

        plt.show()


if __name__ == "__main__":
    main()
