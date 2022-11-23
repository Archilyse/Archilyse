import React, { useState } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { Background } from '../../types';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';
import { usePlanId } from '../../hooks/export';
import Panel from './panel';
import { reloadProject } from './panel-import-annotations-helper';

const UL_STYLE = { paddingRight: '20px', paddingLeft: '20px', marginTop: '10px' };

const PanelImportAnnotationsComponent = ({ currentBackground, currentScaleValidated, floors, projectActions }) => {
  const planId = usePlanId();
  const [selectedFloor, setSelectedFloor] = useState(null);

  const floorIndex = getFloorIndex(floors, planId);

  function onSelect(e) {
    const floorNumber = e.target.value;
    setSelectedFloor(floorNumber);
  }

  function onImport() {
    if (floorIndex[selectedFloor].planReady) {
      reloadProject(floorIndex[selectedFloor].planId, projectActions, currentBackground, currentScaleValidated);
    } else {
      projectActions.showSnackbar({
        message: 'The selected annotation is not ready to be imported',
        severity: 'error',
      });
    }
  }

  const options = Object.keys(floorIndex)
    .sort((a, b) => {
      return Number(a) - Number(b);
    })
    .map(floorNumber => (
      <option key={floorNumber} value={floorNumber}>
        {floorIndex[floorNumber].displayText}
      </option>
    ));
  options.push(<option key={'empty'} value=""></option>);

  return (
    <Panel name={'Import Annotations'} opened={true}>
      <div style={UL_STYLE}>
        <select
          id="select-import-floor"
          style={{ backgroundColor: 'white', width: '80%' }}
          onChange={onSelect}
          value={selectedFloor || ''}
        >
          {options}
        </select>
        <button
          disabled={!selectedFloor}
          style={{ marginTop: '10px', whiteSpace: 'nowrap', marginBottom: '10px', width: '80%' }}
          className="primary-button"
          onClick={onImport}
        >
          Import Annotation
        </button>
      </div>
    </Panel>
  );
};

function getFloorIndex(floors, planId) {
  const currentFloors = floors.filter(floor => floor.plan_id === planId);
  if (currentFloors.length == 0) {
    return {}; // This is a scenario which should only happen in testing
  }
  const currentBuildingId = currentFloors[0].building_id;
  const index = {};
  floors.forEach(floor => {
    if (floor.plan_id != planId && floor.building_id === currentBuildingId) {
      const displayText = floor.plan_ready ? `Floor ${floor.floor_number}` : `Floor ${floor.floor_number} (not ready)`;
      index[floor.floor_number] = { planId: floor.plan_id, displayText: displayText, planReady: floor.plan_ready };
    }
  });
  return index;
}

function mapStateToProps(state) {
  state = state['react-planner'];
  const currentBackground: Background = state.scene.background;
  const floors = state.siteStructure.floors;
  const currentScaleValidated = state.scaleValidated;
  return {
    state,
    currentBackground,
    currentScaleValidated,
    floors,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export const PanelImportAnnotations = connect(mapStateToProps, mapDispatchToProps)(PanelImportAnnotationsComponent);
