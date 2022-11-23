import React, { useRef } from 'react';
import { FormControlLabel, Radio, RadioGroup, TextField } from '@material-ui/core/';
import { capitalize, LoadingIndicator } from 'archilyse-ui-components';
import { Drawer, Dropdown } from '../../components';
import { getBuildingName } from '../../common/modules';
import { QA_MODES } from '../../common/types';
import { CurrentSelection, SimulationValidation } from './QA';
import './controls.scss';

const getUnitOptions = units => [
  { value: '', label: 'Unit' },
  ...units
    .sort((unitA, unitB) => unitA.client_id.localeCompare(unitB.client_id))
    .map(unit => ({
      value: unit.id,
      label: unit.client_id,
    })),
];

const getFloorOptions = floors => [
  { value: '', label: 'Floor' },
  ...floors
    .sort((floorA, floorB) => floorA.floor_number - floorB.floor_number)
    .map(floor => ({
      value: floor.id,
      label: `Floor ${floor.floor_number}`,
    })),
];

const getBuildingOptions = buildings => [
  { value: '', label: 'Building' },
  ...buildings.map(building => ({
    value: building.id,
    label: getBuildingName(building),
  })),
];

const getGroupOptions = groups => [
  { value: '', label: 'Group' },
  ...groups.map(groupName => ({
    value: groupName,
    label: capitalize(groupName),
  })),
];

const getSingleSimulationOptions = simulations => [
  { value: '', label: 'Simulation' },
  ...simulations.map(sim => ({
    value: sim,
    label: sim,
  })),
];

const SimulationDropdown = ({ mode, options, handlers, currentSelection }) => {
  if (mode == QA_MODES.GROUP) {
    return (
      <Dropdown
        className="qa-control-dropdown"
        options={getGroupOptions(options.groups)}
        onChange={handlers.onSelectSimulationGroup}
        value={currentSelection.simulationGroup}
      />
    );
  }
  return (
    <Dropdown
      className="qa-control-dropdown qa-simulation-name-dropdown"
      options={getSingleSimulationOptions(options.simulations)}
      onChange={handlers.onSelectSimulationName}
      value={currentSelection.simulationName}
    />
  );
};

type Props = {
  options: any;
  handlers: any;
  currentSelection: CurrentSelection;
  validationNotes: any;
  isValidated: any;
  validatingHeatmaps: any;
  savingNotes: any;
  simulationValidation: SimulationValidation[];
};

const Controls = ({
  options,
  handlers,
  currentSelection,
  validationNotes = '',
  isValidated,
  validatingHeatmaps,
  savingNotes,
  simulationValidation,
}: Props) => {
  const textAreaEl = useRef(null);
  const { buildings, floors, units } = options;
  const isLoading =
    Object.values(options).some(option => !option) || !currentSelection.simulationMode || !simulationValidation;

  const onErrorClick = (unitId: number) => {
    if (isLoading) return;

    handlers.onSelectUnit({ target: { value: unitId } });
  };

  if (isLoading)
    return (
      <div className="controls">
        <Drawer open={true}>
          <LoadingIndicator className="qa-loading-indicator" />
        </Drawer>
      </div>
    );

  return (
    <div className="controls">
      <Drawer open={true}>
        <div className="control-dropdown">
          <h3 className="slider-title">Simulations </h3>
          <div className="simulation-mode">
            <RadioGroup
              row
              aria-label="simulation-mode"
              name="simulation-mode"
              value={currentSelection.simulationMode}
              onChange={handlers.onSelectSimulationMode}
            >
              <FormControlLabel value={QA_MODES.SINGLE} control={<Radio size={'small'} />} label={'Single'} />
              <FormControlLabel value={QA_MODES.GROUP} control={<Radio size={'small'} />} label={'Group'} />
            </RadioGroup>
          </div>
          <SimulationDropdown
            mode={currentSelection.simulationMode}
            options={options}
            handlers={handlers}
            currentSelection={currentSelection}
          />
        </div>
        <div className="control-dropdown">
          <Dropdown
            className="qa-control-dropdown qa-building-dropdown"
            options={getBuildingOptions(buildings)}
            onChange={handlers.onSelectBuilding}
            value={currentSelection.buildingId}
          />
        </div>
        <div className="control-dropdown">
          <Dropdown
            className="qa-control-dropdown qa-floor-dropdown"
            options={getFloorOptions(floors)}
            onChange={handlers.onSelectFloor}
            value={currentSelection.floorId || ''}
          />
        </div>
        <div className="control-dropdown">
          <Dropdown
            className="qa-control-dropdown qa-unit-dropdown"
            options={getUnitOptions(units)}
            onChange={handlers.onSelectUnit}
            value={currentSelection.unitId || ''}
          />
        </div>

        <div className="notes">
          <h3 className="slider-title">Notes</h3>
          <TextField
            multiline
            inputRef={textAreaEl}
            rows={4}
            rowsMax={4}
            defaultValue={validationNotes}
            placeholder={'Write any site note here'}
          />
          <button
            disabled={savingNotes}
            id={'save_notes_button'}
            className="secondary-button"
            onClick={() => handlers.onSaveNotes(textAreaEl.current.value)}
          >
            {savingNotes ? 'Saving...' : 'Save notes'}
          </button>
        </div>

        {simulationValidation.length > 0 && (
          <div className="simulation-validation-list">
            <h3 className="slider-title">Validation dialog</h3>

            <div className="errors-container">
              <ul className="errors-list">
                {simulationValidation.map(validation => (
                  <li key={validation.id} className="units-errors-item" onClick={() => onErrorClick(validation.id)}>
                    <p className="unit-name">{validation.label}:</p>
                    <ul className="unit-errors-list">
                      {validation.errors.map((error, index) => (
                        <li key={error + index}>{error}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="buttons-continaer">
          <button
            disabled={isValidated || validatingHeatmaps}
            id={'validate_button'}
            className="primary-button"
            onClick={handlers.onValidateHeatmaps}
          >
            {isValidated ? 'Heatmaps validated' : validatingHeatmaps ? 'Saving' : 'Validate Heatmaps'}
          </button>
        </div>
      </Drawer>
    </div>
  );
};

export default Controls;
