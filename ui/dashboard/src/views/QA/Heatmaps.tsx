import React from 'react';
import { Heatmap, LoadingIndicator } from 'archilyse-ui-components';
import { QA_GROUPS, QA_MODES } from '../../common/types';

const { VIEW, SUN, CONNECTIVITY } = QA_GROUPS;

const getGroupSimulations = (simulationGroup, simulations) => {
  if (simulationGroup === VIEW) {
    return simulations.filter(sim => !sim.includes(SUN) && !sim.includes(CONNECTIVITY));
  }
  return simulations.filter(sim => sim.includes(simulationGroup.toLowerCase()));
};

const Heatmaps = ({ currentSelection, siteId, floors = [], units = [], simulations = [] }) => {
  const { buildingId, floorId, unitId, simulationName, simulationMode, simulationGroup } = currentSelection || {};

  const simulationsToDisplay =
    simulationMode === QA_MODES.SINGLE ? [simulationName] : getGroupSimulations(simulationGroup, simulations);

  if ((!unitId && !floorId && !buildingId) || simulations.length === 0)
    return <LoadingIndicator className="qa-loading-indicator" />;

  if (unitId) {
    const selectedUnit = units.find(unit => unit.id == unitId);
    return simulationsToDisplay.map(simulationName => (
      <div key={simulationName}>
        <p className="heatmap-title">{`Unit ${selectedUnit?.client_id} - ${simulationName}`}</p>
        <Heatmap
          key={simulationName}
          unitIds={[unitId]}
          siteId={siteId}
          simulationName={simulationName}
          infoSize="small"
        />
      </div>
    ));
  }

  if (floorId) {
    const selectedFloor = floors.find(floor => floor.id == floorId);
    return simulationsToDisplay.map(simulationName => (
      <div key={simulationName}>
        <p className="heatmap-title">{`Floor ${selectedFloor?.floor_number} - ${simulationName}`}</p>
        <Heatmap
          key={simulationName}
          siteId={siteId}
          planId={selectedFloor?.plan_id}
          unitIds={units.map(unit => unit.id)}
          simulationName={simulationName}
          infoSize="small"
        />
      </div>
    ));
  }

  if (buildingId) {
    if (simulationMode === QA_MODES.GROUP) {
      return <p>Please select a floor or unit to display a group of simulations </p>;
    }
    return floors
      .sort((a, b) => a.floor_number - b.floor_number)
      .map(floor => (
        <div key={floor.floor_number}>
          <p className="heatmap-title">{`Floor ${floor.floor_number} - ${currentSelection.simulationName}`}</p>
          <Heatmap
            key={simulationName}
            siteId={siteId}
            planId={floor.plan_id}
            unitIds={units.filter(unit => unit.floor_id == floor.id).map(u => u.id)}
            simulationName={currentSelection.simulationName}
            infoSize="small"
          />
        </div>
      ));
  }
};

export default Heatmaps;
