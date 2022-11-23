import { SIMULATION_MODE } from 'archilyse-ui-components';
import React from 'react';

type Props = {
  mode: SIMULATION_MODE;
  onModeChange: (newMode: SIMULATION_MODE) => void;
  type: string;
  onTypeChange: (newType: string) => void;
  types: string[];
};

const Controls = ({ mode, onModeChange, type, onTypeChange, types }: Props): JSX.Element => {
  return (
    <>
      <label className="simulation-controls-label">
        Map mode:
        <select
          name="map-mode"
          value={mode}
          onChange={e => onModeChange(e.target.value as SIMULATION_MODE)}
          className="potential-view-input"
        >
          <option value={SIMULATION_MODE.NORMAL}>Map</option>
          <option value={SIMULATION_MODE.SATELLITE}>Satellite</option>
        </select>
      </label>

      <label className="simulation-controls-label">
        Simulation:
        <select
          name="simulation-type"
          value={type}
          onChange={e => onTypeChange(e.target.value)}
          className="potential-view-input"
        >
          {types.map(type => (
            <option key={type}>{type}</option>
          ))}
        </select>
      </label>
    </>
  );
};

export default Controls;
