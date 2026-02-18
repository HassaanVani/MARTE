export interface SolveParams {
  t0_years: number;
  tf_years: number;
  proper_time_years: number;
  mass_kg: number;
}

export interface SolveInputs {
  t0_years: number;
  tf_years: number;
  proper_time_years: number;
  mass_kg: number;
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
}

export interface WorldlineData {
  coord_times_s: number[];
  coord_times_years: number[];
  positions_m: number[][];
  positions_au: number[][];
  proper_times_s: number[];
  proper_times_years: number[];
}

export interface EarthData {
  orbit_radius_au: number;
  departure_position_au: number[];
  arrival_position_au: number[];
  trajectory_times_years: number[];
  trajectory_positions_au: number[][];
}

export interface SolveResponse {
  inputs: SolveInputs;
  solution: SolutionData | null;
  worldline: WorldlineData | null;
  earth: EarthData | null;
  error: string | null;
}
