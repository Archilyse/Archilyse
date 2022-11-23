export type SimulationErrorResult = {
  code: string;
  msg: string;
};

export type SimulationValidResult = {
  [key: string]: number[] | { height: number; lat: number; lon: number }[];
};

type PotentialSimulation = {
  created: string;
  updated: string;
  id: number;
  floor_number: number;
  identifier: string;
  lat: number;
  lon: number;
  layout_mode: string;
  region: string;
  result: SimulationValidResult | SimulationErrorResult;
  simulation_version: string;
  source_surr: string;
  status: string;
  task_id: string;
  type: 'view' | 'sun';
  user_id: number;
};

export default PotentialSimulation;
