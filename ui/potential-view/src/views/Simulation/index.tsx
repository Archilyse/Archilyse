import React, { useEffect, useMemo, useState } from 'react';
import { C } from 'Common';
import { PotentialSimulation, PotentialSimulationInfo } from 'Common/types';
import {
  createRequestState,
  Heatmap,
  Icon,
  LoadingIndicator,
  Navbar,
  NavbarLink,
  RequestStatus,
  SIMULATION_MODE,
} from 'archilyse-ui-components';
import { useParams } from 'react-router';
import './simulation.scss';
import { ProviderRequest } from 'Providers';
import SimulationInfo from '../../components/SimulationInfo';
import Controls from './components/Controls';

const initialSimulationInfo = createRequestState<PotentialSimulationInfo>(null);

const getSimulationTypes = (result: PotentialSimulation['result']): string[] => {
  if (result.msg) return null;

  return Object.keys(result).filter(type => type !== 'observation_points');
};

const findError = (simulationInfo: typeof initialSimulationInfo): [boolean, string] => {
  let [hasError, message] = [false, null];

  if (simulationInfo.status === RequestStatus.REJECTED) {
    [hasError, message] = [true, simulationInfo.error];
  } else if (simulationInfo.status === RequestStatus.FULFILLED && simulationInfo.data.result.msg) {
    [hasError, message] = [true, simulationInfo.data.result.msg];
  }

  return [hasError, message];
};

const links: NavbarLink[] = [{ label: 'Simulations list', url: C.URLS.HOME() }];

const Simulation = () => {
  const { id } = useParams<{ id: string }>();

  const [simulationInfo, dispatch] = useState(initialSimulationInfo);

  const [mapMode, setMapMode] = useState(SIMULATION_MODE.NORMAL);
  const [simulationType, setSimulationType] = useState<string>();

  const fetchSimulationInfo = async () => {
    dispatch({ ...simulationInfo, status: RequestStatus.PENDING });
    try {
      const response = await ProviderRequest.get(C.ENDPOINTS.SIMULATION(id));

      const simulationTypes = getSimulationTypes(response.result);
      if (simulationTypes) setSimulationType(simulationTypes[0]);

      dispatch({ data: response, status: RequestStatus.FULFILLED, error: null });
    } catch (error) {
      const message =
        error.response?.data.message || error.response?.data.msg || 'Error occured while loading simulation';
      dispatch({ ...simulationInfo, status: RequestStatus.REJECTED, error: message });
    }
  };

  useEffect(() => {
    fetchSimulationInfo();
  }, []);

  const simulationTypes = simulationInfo.data && getSimulationTypes(simulationInfo.data.result);
  const [hasError, errorMessage] = findError(simulationInfo);

  const unitIds = useMemo(() => [Number(id)], [id]);

  return (
    <div className="detailed-simulation-container">
      <header className="detailed-simulation-header">
        <Navbar links={links} />

        {simulationTypes && (
          <Controls
            mode={mapMode}
            onModeChange={setMapMode}
            type={simulationType}
            onTypeChange={setSimulationType}
            types={simulationTypes}
          />
        )}

        <div className="simulation-info-container">
          {simulationInfo.status === RequestStatus.FULFILLED && (
            <SimulationInfo simulation={simulationInfo.data} align="column" />
          )}
        </div>
      </header>
      <div className="simulation-map-container">
        {simulationInfo.status === RequestStatus.PENDING && (
          <div className="simulation-loading-container">
            <LoadingIndicator />
            <p>Loading simulation results...</p>
          </div>
        )}
        {hasError && (
          <div className="simulation-result-error-box">
            <Icon>error_outline</Icon>
            <p className="error-message">{errorMessage}</p>
          </div>
        )}
        {simulationInfo.status === RequestStatus.FULFILLED && !hasError && (
          <Heatmap
            simulationName={simulationType}
            unitIds={unitIds}
            heatmapEndpoint={C.ENDPOINTS.SIMULATION_RESULT}
            hexagonRadius={0.8}
            mapSimulationMode={mapMode}
            showMap={true}
            showBrooks={false}
          />
        )}
      </div>
    </div>
  );
};

export default Simulation;
