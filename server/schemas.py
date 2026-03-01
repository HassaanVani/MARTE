"""Pydantic request/response models for the MARTE API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    t0_years: float = Field(default=0.0, ge=0.0, description="Departure time (years)")
    tf_years: float = Field(default=2.0, gt=0.0, description="Arrival time (years)")
    proper_time_years: float = Field(default=1.5, gt=0.0, description="Desired proper time (years)")
    mass_kg: float = Field(default=1000.0, gt=0.0, description="Ship rest mass (kg)")
    trajectory_model: str = Field(
        default="constant_velocity",
        description="Trajectory model: 'constant_velocity' or 'constant_acceleration'",
    )
    proper_acceleration_g: float | None = Field(
        default=None,
        description="Proper acceleration in multiples of g (only for constant_acceleration model)",
    )
    exhaust_velocity_c: float | None = Field(
        default=None,
        description="Exhaust velocity as fraction of c (for fuel budget calculation)",
    )
    elliptical_orbit: bool = Field(
        default=False,
        description="Use elliptical Earth orbit (e=0.017) instead of circular",
    )
    find_all_branches: bool = Field(
        default=False,
        description="Search for all trajectory branches (v2 only)",
    )
    acceleration_profile: str = Field(
        default="step",
        description="Acceleration profile: 'step', 'linear_ramp', or 's_curve' (v2 only)",
    )
    ramp_fraction: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Fraction of each phase used for acceleration ramp (0-0.5)",
    )
    max_acceleration_g: float | None = Field(
        default=None,
        description="G-tolerance limit — max acceleration in multiples of g",
    )
    earth_model: str | None = Field(
        default=None,
        description="Earth orbit model: 'circular', 'elliptical', or 'ephemeris'",
    )
    gr_corrections: bool = Field(
        default=False,
        description="Compute GR (Schwarzschild) proper time corrections",
    )
    compute_perturbation: bool = Field(
        default=False,
        description="Compute multi-body gravitational perturbation analysis",
    )
    target: str = Field(
        default="earth",
        description="Target body: 'earth', 'mercury', 'venus', 'mars', or 'jupiter'",
    )


class SolveInputs(BaseModel):
    t0_years: float
    tf_years: float
    proper_time_years: float
    mass_kg: float
    target: str = "earth"


class SolutionData(BaseModel):
    beta: float
    gamma: float
    speed_m_s: float
    turnaround_time_s: float
    turnaround_time_years: float
    total_proper_time_s: float
    total_proper_time_years: float
    energy_joules: float
    converged: bool
    residual: float
    direction_out: list[float]
    direction_in: list[float]
    arrival_relative_velocity_m_s: list[float]
    arrival_relative_speed_m_s: float
    arrival_relative_speed_beta: float
    # v2 fields (None for v1)
    trajectory_model: str | None = None
    proper_acceleration_m_s2: float | None = None
    peak_beta: float | None = None
    peak_gamma: float | None = None
    phase_boundaries_years: list[float] | None = None


class WorldlineData(BaseModel):
    coord_times_s: list[float]
    coord_times_years: list[float]
    positions_m: list[list[float]]
    positions_au: list[list[float]]
    proper_times_s: list[float]
    proper_times_years: list[float]
    beta_profile: list[float] | None = None


class EarthData(BaseModel):
    orbit_radius_au: float
    departure_position_au: list[float]
    arrival_position_au: list[float]
    trajectory_times_years: list[float]
    trajectory_positions_au: list[list[float]]


class TargetTrajectoryData(BaseModel):
    name: str
    orbit_radius_au: float
    departure_position_au: list[float]
    arrival_position_au: list[float]
    trajectory_times_years: list[float]
    trajectory_positions_au: list[list[float]]


class FuelBudgetData(BaseModel):
    mass_ratio: float
    fuel_mass_fraction: float
    fuel_mass_kg: float
    total_rapidity_change: float
    total_energy_joules: float


class ConvergenceDiagnostics(BaseModel):
    converged: bool
    residual_norm: float
    position_error_m: float
    proper_time_error_s: float
    n_function_evals: int | None = None
    solver_message: str | None = None


class GRDiagnosticsData(BaseModel):
    sr_proper_time_s: float
    sr_proper_time_years: float
    gr_proper_time_s: float
    gr_proper_time_years: float
    delta_tau_s: float
    delta_tau_years: float
    relative_correction: float
    min_distance_from_sun_m: float
    min_distance_from_sun_au: float
    max_gravitational_dilation: float


class PerturbationData(BaseModel):
    max_accel_sun_m_s2: float
    max_accel_jupiter_m_s2: float
    max_accel_saturn_m_s2: float
    total_delta_v_sun_m_s: float
    total_delta_v_jupiter_m_s: float
    total_delta_v_saturn_m_s: float
    closest_approach_sun_m: float
    closest_approach_jupiter_m: float
    closest_approach_saturn_m: float


class BranchData(BaseModel):
    solution: SolutionData
    worldline: WorldlineData


class TargetInfoData(BaseModel):
    name: str
    orbital_radius_au: float
    mass_kg: float | None = None


class SolveResponse(BaseModel):
    inputs: SolveInputs
    solution: SolutionData | None = None
    worldline: WorldlineData | None = None
    earth: EarthData | None = None
    target_trajectory: TargetTrajectoryData | None = None
    error: str | None = None
    fuel_budget: FuelBudgetData | None = None
    convergence: ConvergenceDiagnostics | None = None
    branches: list[BranchData] | None = None
    gr_diagnostics: GRDiagnosticsData | None = None
    perturbation: PerturbationData | None = None


# --- Sweep schemas ---


class Sweep1DRequest(BaseModel):
    base_params: SolveRequest
    param_name: str
    min_value: float
    max_value: float
    steps: int = Field(default=20, le=50, ge=2)


class Sweep2DRequest(BaseModel):
    base_params: SolveRequest
    x_param: str
    x_min: float
    x_max: float
    y_param: str
    y_min: float
    y_max: float
    x_steps: int = Field(default=15, le=30, ge=2)
    y_steps: int = Field(default=15, le=30, ge=2)


class SweepPointData(BaseModel):
    param_value: float | None = None
    x_value: float | None = None
    y_value: float | None = None
    energy: float | None = None
    proper_time_years: float | None = None
    peak_beta: float | None = None
    converged: bool


class Sweep1DResponse(BaseModel):
    swept_param: str
    points: list[SweepPointData]


class Sweep2DResponse(BaseModel):
    x_param: str
    y_param: str
    points: list[SweepPointData]
    x_steps: int
    y_steps: int


# --- Pareto schemas ---


class ParetoRequest(BaseModel):
    t0_years: float = 0.0
    tf_years: float = 2.0
    mass_kg: float = 1000.0
    trajectory_model: str = "constant_velocity"
    proper_acceleration_g: float | None = None
    target: str = "earth"
    n_points: int = Field(default=50, le=100, ge=5)
    earth_model: str | None = None


class ParetoPointData(BaseModel):
    proper_time_years: float
    energy_joules: float
    peak_beta: float


class ParetoResponse(BaseModel):
    points: list[ParetoPointData]
    target: str
