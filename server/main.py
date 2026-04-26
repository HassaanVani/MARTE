"""FastAPI application — thin bridge between the physics engine and the frontend."""

import os

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response

from marte.constants import AU, SPEED_OF_LIGHT, STANDARD_GRAVITY, YEAR
from marte.export import export_csv, export_json
from marte.optimization import compute_pareto_front
from marte.orbital import earth_position
from marte.propulsion import compute_fuel_budget
from marte.relativity import lorentz_factor
from marte.solver import TrajectoryModel, TrajectorySolution, solve_trajectory
from marte.solver_v2 import find_all_solutions
from marte.sweep import sweep_1d, sweep_2d
from marte.targets import TARGETS, target_position

from .schemas import (
    BranchData,
    ConvergenceDiagnostics,
    EarthData,
    FuelBudgetData,
    GRDiagnosticsData,
    ParetoPointData,
    ParetoRequest,
    ParetoResponse,
    PerturbationData,
    SolutionData,
    SolveInputs,
    SolveRequest,
    SolveResponse,
    Sweep1DRequest,
    Sweep1DResponse,
    Sweep2DRequest,
    Sweep2DResponse,
    SweepPointData,
    TargetInfoData,
    TargetTrajectoryData,
    WorldlineData,
)

app = FastAPI(title="MARTE API", version="0.1.0")

# CORS: allow local dev and any configured production origins
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_origins = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_solution_data(sol: TrajectorySolution) -> tuple[SolutionData, WorldlineData]:
    """Build API response models from a TrajectorySolution."""
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

    return solution, worldline


def _build_convergence(sol: TrajectorySolution) -> ConvergenceDiagnostics:
    """Build convergence diagnostics from a TrajectorySolution."""
    return ConvergenceDiagnostics(
        converged=sol.converged,
        residual_norm=sol.residual,
        position_error_m=sol.position_error_m,
        proper_time_error_s=sol.proper_time_error_s,
        n_function_evals=sol.n_function_evals,
        solver_message=sol.solver_message,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/targets")
def get_targets() -> list[TargetInfoData]:
    """Return list of available planetary targets."""
    return [
        TargetInfoData(
            name=tgt.name,
            orbital_radius_au=tgt.orbital_radius_au,
            mass_kg=tgt.mass_kg,
        )
        for tgt in TARGETS.values()
    ]


@app.post("/api/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    inputs = SolveInputs(
        t0_years=req.t0_years,
        tf_years=req.tf_years,
        proper_time_years=req.proper_time_years,
        mass_kg=req.mass_kg,
        target=req.target,
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

    elliptical = req.elliptical_orbit
    earth_model = req.earth_model

    # If earth_model is "ephemeris", pre-load the ephemeris data
    if earth_model == "ephemeris":
        from marte.orbital import load_ephemeris
        # Add margin around the time range
        margin = 30 * 86400  # 30 days
        load_ephemeris(t0_s - margin, tf_s + margin, step_days=1)

    # G-tolerance validation
    if req.max_acceleration_g is not None and proper_accel is not None:
        max_accel = req.max_acceleration_g * STANDARD_GRAVITY
        if proper_accel > max_accel:
            proper_accel = max_accel

    try:
        sol = solve_trajectory(
            t0_s, tf_s, tau_s, req.mass_kg,
            model=model,
            proper_acceleration=proper_accel,
            elliptical=elliptical,
            acceleration_profile=req.acceleration_profile,
            ramp_fraction=req.ramp_fraction,
            earth_model=earth_model,
            gr_corrections=req.gr_corrections,
            compute_perturbation=req.compute_perturbation,
            target=req.target,
        )
    except ValueError as e:
        return SolveResponse(inputs=inputs, error=str(e))

    solution, worldline = _build_solution_data(sol)
    convergence = _build_convergence(sol)

    # Sample Earth trajectory
    n_samples = 100
    t_samples = np.linspace(t0_s, tf_s, n_samples)
    earth_positions = [
        earth_position(t, elliptical=elliptical, earth_model=earth_model)
        for t in t_samples
    ]

    r_e0 = earth_position(t0_s, elliptical=elliptical, earth_model=earth_model)
    r_ef = earth_position(tf_s, elliptical=elliptical, earth_model=earth_model)

    earth = EarthData(
        orbit_radius_au=1.0,
        departure_position_au=(r_e0 / AU).tolist(),
        arrival_position_au=(r_ef / AU).tolist(),
        trajectory_times_years=(t_samples / YEAR).tolist(),
        trajectory_positions_au=[(p / AU).tolist() for p in earth_positions],
    )

    # Target trajectory (when target != earth)
    target_trajectory_data = None
    if req.target.lower() != "earth":
        tgt = TARGETS.get(req.target.lower())
        if tgt:
            target_positions = [target_position(req.target, t) for t in t_samples]
            r_t0 = target_position(req.target, t0_s)
            r_tf = target_position(req.target, tf_s)
            target_trajectory_data = TargetTrajectoryData(
                name=tgt.name,
                orbit_radius_au=tgt.orbital_radius_au,
                departure_position_au=(r_t0 / AU).tolist(),
                arrival_position_au=(r_tf / AU).tolist(),
                trajectory_times_years=(t_samples / YEAR).tolist(),
                trajectory_positions_au=[(p / AU).tolist() for p in target_positions],
            )

    # Fuel budget (if exhaust velocity provided)
    fuel_budget = None
    if req.exhaust_velocity_c is not None and req.exhaust_velocity_c > 0:
        exhaust_vel = req.exhaust_velocity_c * SPEED_OF_LIGHT
        fb = compute_fuel_budget(sol.total_rapidity_change, exhaust_vel, req.mass_kg)
        fuel_budget = FuelBudgetData(
            mass_ratio=fb.mass_ratio,
            fuel_mass_fraction=fb.fuel_mass_fraction,
            fuel_mass_kg=fb.fuel_mass_kg,
            total_rapidity_change=fb.total_delta_v,
            total_energy_joules=fb.total_energy_joules,
        )

    # Multi-solution branches (v2 only)
    branches = None
    if req.find_all_branches and model == TrajectoryModel.CONSTANT_ACCELERATION:
        all_sols = find_all_solutions(
            t0_s, tf_s, tau_s, req.mass_kg,
            proper_acceleration=proper_accel,
            elliptical=elliptical,
            acceleration_profile=req.acceleration_profile,
            ramp_fraction=req.ramp_fraction,
            earth_model=earth_model,
            gr_corrections=req.gr_corrections,
            compute_perturbation=req.compute_perturbation,
            target=req.target,
        )
        if len(all_sols) > 0:
            branches = []
            for branch_sol in all_sols:
                b_solution, b_worldline = _build_solution_data(branch_sol)
                branches.append(BranchData(solution=b_solution, worldline=b_worldline))
            # Primary solution = first branch
            if branches:
                solution = branches[0].solution
                worldline = branches[0].worldline
                convergence = _build_convergence(all_sols[0])

    # GR diagnostics (from primary solution)
    gr_diagnostics_data = None
    if sol.gr_diagnostics is not None:
        grd = sol.gr_diagnostics
        gr_diagnostics_data = GRDiagnosticsData(
            sr_proper_time_s=grd.sr_proper_time_s,
            sr_proper_time_years=grd.sr_proper_time_s / YEAR,
            gr_proper_time_s=grd.gr_proper_time_s,
            gr_proper_time_years=grd.gr_proper_time_s / YEAR,
            delta_tau_s=grd.delta_tau_s,
            delta_tau_years=grd.delta_tau_s / YEAR,
            relative_correction=grd.relative_correction,
            min_distance_from_sun_m=grd.min_distance_from_sun_m,
            min_distance_from_sun_au=grd.min_distance_from_sun_m / AU,
            max_gravitational_dilation=grd.max_gravitational_dilation,
        )

    # Perturbation data
    perturbation_data = None
    if sol.perturbation is not None:
        pa = sol.perturbation
        perturbation_data = PerturbationData(
            max_accel_sun_m_s2=pa.max_accel_sun,
            max_accel_jupiter_m_s2=pa.max_accel_jupiter,
            max_accel_saturn_m_s2=pa.max_accel_saturn,
            total_delta_v_sun_m_s=pa.total_delta_v_sun,
            total_delta_v_jupiter_m_s=pa.total_delta_v_jupiter,
            total_delta_v_saturn_m_s=pa.total_delta_v_saturn,
            closest_approach_sun_m=pa.closest_approach_sun,
            closest_approach_jupiter_m=pa.closest_approach_jupiter,
            closest_approach_saturn_m=pa.closest_approach_saturn,
        )

    return SolveResponse(
        inputs=inputs,
        solution=solution,
        worldline=worldline,
        earth=earth,
        target_trajectory=target_trajectory_data,
        fuel_budget=fuel_budget,
        convergence=convergence,
        branches=branches,
        gr_diagnostics=gr_diagnostics_data,
        perturbation=perturbation_data,
    )


def _solve_from_request(req: SolveRequest) -> TrajectorySolution:
    """Solve trajectory from a SolveRequest (shared by solve + export)."""
    t0_s = req.t0_years * YEAR
    tf_s = req.tf_years * YEAR
    tau_s = req.proper_time_years * YEAR

    model = TrajectoryModel.CONSTANT_VELOCITY
    proper_accel = None
    if req.trajectory_model == "constant_acceleration":
        model = TrajectoryModel.CONSTANT_ACCELERATION
        proper_accel = (req.proper_acceleration_g or 1.0) * STANDARD_GRAVITY

    earth_model = req.earth_model
    if earth_model == "ephemeris":
        from marte.orbital import load_ephemeris
        margin = 30 * 86400
        load_ephemeris(t0_s - margin, tf_s + margin, step_days=1)

    if req.max_acceleration_g is not None and proper_accel is not None:
        max_accel = req.max_acceleration_g * STANDARD_GRAVITY
        if proper_accel > max_accel:
            proper_accel = max_accel

    return solve_trajectory(
        t0_s, tf_s, tau_s, req.mass_kg,
        model=model,
        proper_acceleration=proper_accel,
        elliptical=req.elliptical_orbit,
        acceleration_profile=req.acceleration_profile,
        ramp_fraction=req.ramp_fraction,
        earth_model=earth_model,
        gr_corrections=req.gr_corrections,
        compute_perturbation=req.compute_perturbation,
        target=req.target,
    )


@app.post("/api/export/json")
def export_json_endpoint(req: SolveRequest) -> Response:
    """Solve and return trajectory as JSON file."""
    sol = _solve_from_request(req)
    params = req.model_dump()
    content = export_json(sol, params)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=marte_trajectory.json"},
    )


@app.post("/api/export/csv")
def export_csv_endpoint(req: SolveRequest) -> PlainTextResponse:
    """Solve and return worldline as CSV file."""
    sol = _solve_from_request(req)
    content = export_csv(sol)
    return PlainTextResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=marte_worldline.csv"},
    )


@app.post("/api/sweep/1d", response_model=Sweep1DResponse)
def sweep_1d_endpoint(req: Sweep1DRequest) -> Sweep1DResponse:
    """Run 1D parameter sweep."""
    import numpy as np_

    steps = min(req.steps, 50)
    values = np_.linspace(req.min_value, req.max_value, steps).tolist()
    base = req.base_params.model_dump()
    result = sweep_1d(base, req.param_name, values, target=base.get("target", "earth"))

    points = []
    for i, pt in enumerate(result.points):
        points.append(SweepPointData(
            param_value=values[i],
            energy=pt.energy,
            proper_time_years=pt.proper_time_s / YEAR if pt.proper_time_s else None,
            peak_beta=pt.peak_beta,
            converged=pt.converged,
        ))

    return Sweep1DResponse(swept_param=result.swept_param, points=points)


@app.post("/api/sweep/2d", response_model=Sweep2DResponse)
def sweep_2d_endpoint(req: Sweep2DRequest) -> Sweep2DResponse:
    """Run 2D parameter sweep."""
    import numpy as np_

    x_steps = min(req.x_steps, 30)
    y_steps = min(req.y_steps, 30)
    x_values = np_.linspace(req.x_min, req.x_max, x_steps).tolist()
    y_values = np_.linspace(req.y_min, req.y_max, y_steps).tolist()
    base = req.base_params.model_dump()
    result = sweep_2d(
        base, req.x_param, x_values, req.y_param, y_values,
        target=base.get("target", "earth"),
    )

    points = []
    for yi, row in enumerate(result.grid):
        for xi, pt in enumerate(row):
            points.append(SweepPointData(
                x_value=x_values[xi],
                y_value=y_values[yi],
                energy=pt.energy,
                proper_time_years=pt.proper_time_s / YEAR if pt.proper_time_s else None,
                peak_beta=pt.peak_beta,
                converged=pt.converged,
            ))

    return Sweep2DResponse(
        x_param=result.x_param,
        y_param=result.y_param,
        points=points,
        x_steps=x_steps,
        y_steps=y_steps,
    )


@app.post("/api/pareto", response_model=ParetoResponse)
def pareto_endpoint(req: ParetoRequest) -> ParetoResponse:
    """Compute Pareto front of energy vs proper time."""
    t0_s = req.t0_years * YEAR
    tf_s = req.tf_years * YEAR

    proper_accel = None
    if req.proper_acceleration_g is not None:
        proper_accel = req.proper_acceleration_g * STANDARD_GRAVITY

    front = compute_pareto_front(
        t0=t0_s,
        tf=tf_s,
        mass=req.mass_kg,
        model=req.trajectory_model,
        proper_acceleration=proper_accel,
        target=req.target,
        n_points=min(req.n_points, 100),
        earth_model=req.earth_model,
    )

    return ParetoResponse(
        points=[
            ParetoPointData(
                proper_time_years=pt.proper_time_years,
                energy_joules=pt.energy_joules,
                peak_beta=pt.peak_beta,
            )
            for pt in front.points
        ],
        target=front.target,
    )
