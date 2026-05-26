import sys
from marte.solver import solve_trajectory
from marte.constants import YEAR

try:
    sol = solve_trajectory(
        0.0,
        1.5 * YEAR,
        1.0 * YEAR,
        2000.0,
        target="mars"
    )
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
