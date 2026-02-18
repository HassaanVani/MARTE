"""FastAPI application — thin bridge between the physics engine and the frontend."""

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from marte.constants import AU, SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.orbital import earth_position
from marte.relativity import lorentz_factor
from marte.solver import TrajectoryModel, solve_trajectory

from .schemas import (
    EarthData,
    SolutionData,
    SolveInputs,
    SolveRequest,
    SolveResponse,
    WorldlineData,
)

app = FastAPI(title="MARTE API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    inputs = SolveInputs(
        t0_years=req.t0_years,
        tf_years=req.tf_years,
        proper_time_years=req.proper_time_years,
        mass_kg=req.mass_kg,
    )

    t0_s = req.t0_years * YEAR
    tf_s = req.tf_years * YEAR
    tau_s = req.proper_time_years * YEAR

    # Model selection
    model = TrajectoryModel.CONSTANT_VELOCITY
    proper_accel = None
    if req.trajectory_model == "constant_acceleration":
        model = TrajectoryModel.CONSTANT_ACCELERATION
        proper_accel = (req.proper_acceleration_g or 1.0) * STANDARD_GRAVITY

    try:
        sol = solve_trajectory(
            t0_s, tf_s, tau_s, req.mass_kg,
            model=model,
            proper_acceleration=proper_accel,
        )
    except ValueError as e:
        return SolveResponse(inputs=inputs, error=str(e))

    beta = sol.velocity_magnitude
    gamma = lorentz_factor(beta)
    speed = beta * SPEED_OF_LIGHT

    wl = sol.worldline
    positions_m = wl.positions.tolist()
    positions_au = (wl.positions / AU).tolist()

    arrival_rel_speed = float(np.linalg.norm(sol.arrival_relative_velocity))

    solution = SolutionData(
        beta=beta,
        gamma=gamma,
        speed_m_s=speed,
        turnaround_time_s=sol.turnaround_time,
        turnaround_time_years=sol.turnaround_time / YEAR,
        total_proper_time_s=sol.total_proper_time,
        total_proper_time_years=sol.total_proper_time / YEAR,
        energy_joules=sol.energy,
        converged=sol.converged,
        residual=sol.residual,
        direction_out=sol.direction_out.tolist(),
        direction_in=sol.direction_in.tolist(),
        arrival_relative_velocity_m_s=sol.arrival_relative_velocity.tolist(),
        arrival_relative_speed_m_s=arrival_rel_speed,
        arrival_relative_speed_beta=arrival_rel_speed / SPEED_OF_LIGHT,
        trajectory_model=sol.trajectory_model.value,
        proper_acceleration_m_s2=sol.proper_acceleration,
        peak_beta=sol.peak_beta,
        peak_gamma=sol.peak_gamma,
        phase_boundaries_years=(
            [t / YEAR for t in sol.phase_boundaries]
            if sol.phase_boundaries
            else None
        ),
    )

    worldline = WorldlineData(
        coord_times_s=wl.coord_times.tolist(),
        coord_times_years=(wl.coord_times / YEAR).tolist(),
        positions_m=positions_m,
        positions_au=positions_au,
        proper_times_s=wl.proper_times.tolist(),
        proper_times_years=(wl.proper_times / YEAR).tolist(),
        beta_profile=sol.beta_profile if sol.beta_profile else None,
    )

    # Sample Earth trajectory
    n_samples = 100
    t_samples = np.linspace(t0_s, tf_s, n_samples)
    earth_positions = [earth_position(t) for t in t_samples]

    r_e0 = earth_position(t0_s)
    r_ef = earth_position(tf_s)

    earth = EarthData(
        orbit_radius_au=1.0,
        departure_position_au=(r_e0 / AU).tolist(),
        arrival_position_au=(r_ef / AU).tolist(),
        trajectory_times_years=(t_samples / YEAR).tolist(),
        trajectory_positions_au=[(p / AU).tolist() for p in earth_positions],
    )

    return SolveResponse(
        inputs=inputs,
        solution=solution,
        worldline=worldline,
        earth=earth,
    )
