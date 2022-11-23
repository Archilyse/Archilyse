const NON_SIMULATION_NAMES_FIELDS = ['observation_points', 'resolution'];
const getSimulationNames = unitHeatmapsResponse =>
  Object.keys(unitHeatmapsResponse || []).filter(v => !NON_SIMULATION_NAMES_FIELDS.includes(v));

export default getSimulationNames;
