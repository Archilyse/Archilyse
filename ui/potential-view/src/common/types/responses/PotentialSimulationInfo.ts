import PotentialSimulation from './PotentialSimulation';

type PotentialSimulationInfo = Pick<
  PotentialSimulation,
  'id' | 'created' | 'lat' | 'lon' | 'floor_number' | 'type' | 'result'
>;

export default PotentialSimulationInfo;
