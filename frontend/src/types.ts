export interface SolveParams {
  t0_years: number;
  tf_years: number;
  proper_time_years: number;
  mass_kg: number;
  trajectory_model: string;
  proper_acceleration_g: number | null;
  exhaust_velocity_c: number | null;
  elliptical_orbit: boolean;
  find_all_branches: boolean;
  acceleration_profile: string;
  ramp_fraction: number;
  max_acceleration_g: number | null;
  earth_model: string | null;
  gr_corrections: boolean;
  compute_perturbation: boolean;
  target: string;
}

export interface SolveInputs {
  t0_years: number;
  tf_years: number;
  proper_time_years: number;
  mass_kg: number;
  target: string;
}

export interface SolutionData {
  beta: number;
  gamma: number;
  speed_m_s: number;
  turnaround_time_s: number;
  turnaround_time_years: number;
  total_proper_time_s: number;
  total_proper_time_years: number;
  energy_joules: number;
  converged: boolean;
  residual: number;
  direction_out: number[];
  direction_in: number[];
  arrival_relative_velocity_m_s: number[];
  arrival_relative_speed_m_s: number;
  arrival_relative_speed_beta: number;
  trajectory_model: string | null;
  proper_acceleration_m_s2: number | null;
  peak_beta: number | null;
  peak_gamma: number | null;
  phase_boundaries_years: number[] | null;
}

export interface WorldlineData {
  coord_times_s: number[];
  coord_times_years: number[];
  positions_m: number[][];
  positions_au: number[][];
  proper_times_s: number[];
  proper_times_years: number[];
  beta_profile: number[] | null;
}

export interface EarthData {
  orbit_radius_au: number;
  departure_position_au: number[];
  arrival_position_au: number[];
  trajectory_times_years: number[];
  trajectory_positions_au: number[][];
}

export interface FuelBudgetData {
  mass_ratio: number;
  fuel_mass_fraction: number;
  fuel_mass_kg: number;
  total_rapidity_change: number;
  total_energy_joules: number;
}

export interface ConvergenceDiagnostics {
  converged: boolean;
  residual_norm: number;
  position_error_m: number;
  proper_time_error_s: number;
  n_function_evals: number | null;
  solver_message: string | null;
}

export interface GRDiagnosticsData {
  sr_proper_time_s: number;
  sr_proper_time_years: number;
  gr_proper_time_s: number;
  gr_proper_time_years: number;
  delta_tau_s: number;
  delta_tau_years: number;
  relative_correction: number;
  min_distance_from_sun_m: number;
  min_distance_from_sun_au: number;
  max_gravitational_dilation: number;
}

export interface PerturbationData {
  max_accel_sun_m_s2: number;
  max_accel_jupiter_m_s2: number;
  max_accel_saturn_m_s2: number;
  total_delta_v_sun_m_s: number;
  total_delta_v_jupiter_m_s: number;
  total_delta_v_saturn_m_s: number;
  closest_approach_sun_m: number;
  closest_approach_jupiter_m: number;
  closest_approach_saturn_m: number;
}

export interface BranchData {
  solution: SolutionData;
  worldline: WorldlineData;
}

export interface TargetTrajectoryData {
  name: string;
  orbit_radius_au: number;
  departure_position_au: number[];
  arrival_position_au: number[];
  trajectory_times_years: number[];
  trajectory_positions_au: number[][];
}

export interface TargetInfoData {
  name: string;
  orbital_radius_au: number;
  mass_kg: number | null;
}

export interface SolveResponse {
  inputs: SolveInputs;
  solution: SolutionData | null;
  worldline: WorldlineData | null;
  earth: EarthData | null;
  target_trajectory: TargetTrajectoryData | null;
  error: string | null;
  fuel_budget: FuelBudgetData | null;
  convergence: ConvergenceDiagnostics | null;
  branches: BranchData[] | null;
  gr_diagnostics: GRDiagnosticsData | null;
  perturbation: PerturbationData | null;
}

export type ViewMode = "observer" | "kinetic" | "planning";

// --- Sweep types ---

export interface Sweep1DConfig {
  param_name: string;
  min_value: number;
  max_value: number;
  steps: number;
}

export interface Sweep2DConfig {
  x_param: string;
  x_min: number;
  x_max: number;
  y_param: string;
  y_min: number;
  y_max: number;
  x_steps: number;
  y_steps: number;
}

export interface SweepPointData {
  param_value: number | null;
  x_value: number | null;
  y_value: number | null;
  energy: number | null;
  proper_time_years: number | null;
  peak_beta: number | null;
  converged: boolean;
}

export interface Sweep1DResult {
  swept_param: string;
  points: SweepPointData[];
}

export interface Sweep2DResult {
  x_param: string;
  y_param: string;
  points: SweepPointData[];
  x_steps: number;
  y_steps: number;
}

// --- Pareto types ---

export interface ParetoConfig {
  t0_years: number;
  tf_years: number;
  mass_kg: number;
  trajectory_model: string;
  proper_acceleration_g: number | null;
  target: string;
  n_points: number;
  earth_model: string | null;
}

export interface ParetoPointData {
  proper_time_years: number;
  energy_joules: number;
  peak_beta: number;
}

export interface ParetoResult {
  points: ParetoPointData[];
  target: string;
}

export interface AnimationState {
  progress: number;
  playing: boolean;
  speed: number;
}

export interface InterpolatedState {
  coordTime: number;
  properTime: number;
  positionAU: [number, number, number];
  beta: number;
  gamma: number;
  velocityDirection: [number, number, number];
  phase: "ACCELERATING" | "COASTING" | "TURNAROUND" | "DECELERATING";
  distanceToEarth: number;
  earthPositionAU: [number, number, number];
  earthApparentPositionAU: [number, number, number];
  lightDelaySeconds: number;
}
