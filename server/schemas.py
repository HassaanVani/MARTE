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


class SolveInputs(BaseModel):
    t0_years: float
    tf_years: float
    proper_time_years: float
    mass_kg: float


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


class SolveResponse(BaseModel):
    inputs: SolveInputs
    solution: SolutionData | None = None
    worldline: WorldlineData | None = None
    earth: EarthData | None = None
    error: str | None = None
    solutions: list[SolutionData] | None = None
