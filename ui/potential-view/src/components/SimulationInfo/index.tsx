import React from 'react';
import cn from 'classnames';
import { PotentialSimulationInfo } from 'Common/types';
import './simulationInfo.scss';
import { DateUtils } from 'archilyse-ui-components';

type Props = {
  simulation: PotentialSimulationInfo;
  align: 'row' | 'column';
};

const SimulationInfo = ({ simulation, align }: Props): JSX.Element => {
  if (!simulation) return null;

  return (
    <>
      <div className={cn('simulation-info-section', align)}>
        <p className="simulation-info-line">Lat: {simulation.lat}</p>
        <p className="simulation-info-line">Lon: {simulation.lon}</p>
      </div>
      <div className={cn('simulation-info-section', align)}>
        <p className="simulation-info-line">Floor: {simulation.floor_number}</p>
        <p className="simulation-info-line">Type: {simulation.type.toUpperCase()}</p>
      </div>
      <div className={cn('simulation-info-section', align)}>
        <p className="simulation-info-line">Date: {DateUtils.getDateFromISOString(simulation.created)}</p>
        <p className="simulation-info-line">Time: {DateUtils.getTimeFromISOString(simulation.created)}</p>
      </div>
    </>
  );
};

export default SimulationInfo;
