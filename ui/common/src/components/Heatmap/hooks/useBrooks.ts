import { useEffect, useState } from 'react';
import C from '../../../constants';
import { ProviderRequest } from '../../../providers';
import { BrooksType, SIMULATION_TYPES } from '../../../types';
import { RequestStateType, RequestStatus } from '../../../types/RequestStateType';
import { cleanBrooks, cleanHeatmap } from '../../SimulationViewer/libs/SimRenderer';
import BrooksRenderer from '../libs/BrooksRenderer';
import { HeatmapHarpMapControls } from './useHarpMap';

const initialState: RequestStateType<BrooksType> = {
  data: null,
  status: RequestStatus.IDLE,
  error: null,
};

type Props = {
  planId: number;
  unitIds: number[];
  mapControls: HeatmapHarpMapControls;
  heatmapType: SIMULATION_TYPES;
  showBrooks: boolean;
};

const useBrooks = ({ planId, unitIds, mapControls, heatmapType, showBrooks }: Props) => {
  const [state, dispatch] = useState<RequestStateType<BrooksType>>(initialState);

  const fetchBrooks = async () => {
    dispatch({ ...state, status: RequestStatus.PENDING });
    try {
      const endpoint = planId ? C.ENDPOINTS.PLAN_BROOKS_SIMPLE(planId) : C.ENDPOINTS.UNIT_BROOKS_SIMPLE(unitIds);

      const result = await ProviderRequest.getCached(endpoint);

      dispatch({ status: RequestStatus.FULFILLED, data: result, error: null });
    } catch (error) {
      dispatch({ ...state, status: RequestStatus.REJECTED, error: 'Error while loading brooks' });
    }
  };

  useEffect(() => {
    if (mapControls.map && state.data) {
      cleanHeatmap(mapControls.map);
      cleanBrooks(mapControls.map);
    }

    if (showBrooks) fetchBrooks();
  }, [planId, unitIds]);

  useEffect(() => {
    if (state.status === RequestStatus.FULFILLED && state.data && mapControls) {
      const displayConnectivity = heatmapType === SIMULATION_TYPES.CONNECTIVITY;

      const { data: brooksData } = state;
      BrooksRenderer.drawBrooks(brooksData, mapControls, displayConnectivity);
    }
  }, [state, heatmapType, mapControls]);

  return { brooks: state };
};

export default useBrooks;
