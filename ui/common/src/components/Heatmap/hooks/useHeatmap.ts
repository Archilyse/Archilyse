import { useEffect, useState } from 'react';
import { PATRIZIA_SITES_IDS } from '../../../constants';
import { ProviderRequest } from '../../../providers';
import { HeatmapsType, SIMULATION_TYPES } from '../../../types';
import { RequestStateType, RequestStatus } from '../../../types/RequestStateType';
import { extractSimulations } from '../../SimulationViewer/libs/AnnotationsRenderer';
import { calculateDomain, cleanHeatmap } from '../../SimulationViewer/libs/SimRenderer';
import { HeatmapStatistics } from '../components/StatisticsInfo';
import HeatmapRenderer from '../libs/HeatmapRenderer';
import HeatmapStatisticsUtils from '../libs/HeatmapStatisticsUtils';
import { HeatmapHarpMapControls } from './useHarpMap';

const initialState: RequestStateType<HeatmapsType> = {
  data: { observation_points: { total: [], local: [] }, resolution: null, heatmaps: [] },
  status: RequestStatus.IDLE,
  error: null,
};

type Props = {
  unitIds: number[];
  siteId?: number;
  simulationName: string;
  mapControls: HeatmapHarpMapControls;
  rotationToNorth: number;
  endpoint: (...args) => string;
  hexagonRadius?: number;
  showMap: boolean;
};

const useHeatmap = ({
  siteId = undefined,
  unitIds,
  mapControls,
  simulationName = '',
  rotationToNorth = 0,
  endpoint,
  hexagonRadius: propsHexagonRadius,
  showMap,
}: Props) => {
  const [state, dispatch] = useState(initialState);
  const [statistics, setStatistics] = useState<HeatmapStatistics>(null);

  const fetchHeatmap = async () => {
    dispatch({ ...state, status: RequestStatus.PENDING });
    try {
      let type = SIMULATION_TYPES.VIEW_SUN;
      if (simulationName.includes(SIMULATION_TYPES.CONNECTIVITY)) type = SIMULATION_TYPES.CONNECTIVITY;
      if (simulationName.includes(SIMULATION_TYPES.NOISE)) type = SIMULATION_TYPES.NOISE;

      const requests = unitIds.map(unitId => ProviderRequest.getCached(endpoint(unitId, type.toUpperCase())));

      const heatmaps: HeatmapsType[] = await Promise.all(requests);
      const result = extractSimulations(heatmaps);

      dispatch({ status: RequestStatus.FULFILLED, data: result, error: null });
    } catch (error) {
      dispatch({ ...state, status: RequestStatus.REJECTED, error: 'Error while loading brooks' });
    }
  };

  useEffect(() => {
    if (mapControls.map && state.data) cleanHeatmap(mapControls.map);

    fetchHeatmap();
  }, [unitIds, simulationName]);

  useEffect(() => {
    if (state.status === RequestStatus.FULFILLED) {
      const heatmaps = state.data.heatmaps.reduce((accum, simulation) => {
        const heatmapValues = simulation?.[simulationName] || [];
        return [...accum, ...heatmapValues];
      }, []);
      const [min, max, mean] = HeatmapStatisticsUtils.getSimulationMeaningfulPoints(heatmaps, simulationName);
      const _statistics = HeatmapStatisticsUtils.calculateSimulationDistribution(heatmaps, [min, max, mean]);
      setStatistics(_statistics);

      state.data.heatmaps.forEach((simulation, index) => {
        const heatmap = simulation[simulationName];

        if (heatmap && mapControls) {
          try {
            const { observation_points, resolution } = state.data;
            const localObservationPoints = observation_points.local[index];
            const totalObservationPoints = observation_points.total;

            const hexagonRadius = PATRIZIA_SITES_IDS.includes(Number(siteId))
              ? 0.23
              : propsHexagonRadius || HeatmapRenderer.getRadiusByResolution(resolution);

            const valueToColor = calculateDomain(min, max);
            const options = { rotationToNorth, hexagonRadius, showMap };

            HeatmapRenderer.drawHeatmap(
              heatmap,
              localObservationPoints,
              totalObservationPoints,
              mapControls,
              valueToColor,
              options
            );
          } catch (error) {
            console.log('Error occurred while drawing a heatmap', error);
          }
        }
      });
    }
  }, [state, simulationName, mapControls]);

  return { heatmap: state, statistics };
};

export default useHeatmap;
