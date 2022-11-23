import React from 'react';
import cn from 'classnames';
import { Link } from 'react-router-dom';
import { Icon, LoadingIndicator, RequestStateType, RequestStatus } from 'archilyse-ui-components';
import SimulationInfo from 'Components/SimulationInfo';
import { PotentialSimulation } from 'Common/types';
import C from 'Common/constants';
import './simulationsList.scss';

const CLASSNAME_BY_STATUS = {
  SUCCESS: 'green',
  FAILURE: 'red',
  PROCESSING: 'orange',
  PENDING: 'pending',
};

type Props = {
  simulations: RequestStateType<PotentialSimulation[]>;
};

const SimulationsList = ({ simulations }: Props): JSX.Element => {
  if (simulations.status === RequestStatus.PENDING) {
    return (
      <div className="simulations-list loading">
        <div className="simulations-loading-container">
          <LoadingIndicator />
          <p>Loading simulations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="simulations-list">
      {simulations.data.map(simulation => (
        <div key={simulation.id} className="simulation-info-card">
          <SimulationInfo simulation={simulation} align="row" />
          <div className="simulation-info-section result">
            <p className="simulation-info-line">
              Status:
              <span className={cn('simulation-status', CLASSNAME_BY_STATUS[simulation.status])}>
                {simulation.status}
              </span>
              {simulation.status === 'FAILURE' && (
                <span>
                  <Icon>error_outline</Icon>
                </span>
              )}
            </p>
            {simulation.status === 'SUCCESS' && (
              <Link to={C.URLS.SIMULATION_VIEW(simulation.id)} className="simulation-view-link">
                View result
              </Link>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default SimulationsList;
