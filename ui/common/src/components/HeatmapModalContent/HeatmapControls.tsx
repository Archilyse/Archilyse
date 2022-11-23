import React from 'react';
import { RequestStateType, RequestStatus, Unit } from '../../types';
import Dropdown from '../Dropdown';
import Icon from '../Icon';
import { LoadingIndicator } from '..';
import HeatmapModalUtils from './HeatmapModalUtils';
import { SiteStructureState } from './useHeatmaps';
import { HeatmapModalContentProps, HeatmapsSelectedFilters } from '.';

const ICON_STYLE = {
  marginLeft: 0,
  marginRight: '5px',
};

const LOADING_STYLE = {
  width: 15,
  height: 15,
};

export type HeatmapControlsProps = {
  selected: HeatmapsSelectedFilters;
  siteStructure: SiteStructureState;
  simulationDimensions: RequestStateType<string[]>;
  siteUnits: Unit[];
  extraLeftFilters?: JSX.Element;
  extraRightFilters?: JSX.Element;
  onChange: (selected: HeatmapsSelectedFilters) => void;
} & Pick<HeatmapModalContentProps, 'dropdowns' | 'showDropdownLabel'>;

const getDropdownOptions = (array, { label, value }) =>
  array.map(item => ({
    label: typeof label === 'string' ? item[label] : label(item),
    value: typeof value === 'string' ? item[value] : value(item),
  }));

const HeatmapControls = ({
  selected,
  siteStructure,
  simulationDimensions,
  siteUnits,
  dropdowns,
  showDropdownLabel,
  extraLeftFilters,
  extraRightFilters,
  onChange,
}: HeatmapControlsProps): JSX.Element => {
  const handleDimensionChange = event => {
    onChange({ ...selected, dimension: event.target.value });
  };

  const handleBuildingChange = event => {
    const newBuilding = event.target.value;
    const floors = HeatmapModalUtils.filterFloorsByBuilding(siteStructure.floors, newBuilding);
    const firstPositiveFloorId = HeatmapModalUtils.findPositiveFloorId(floors);
    const firstFloorId = floors[0].id;

    onChange({
      ...selected,
      building: newBuilding,
      floor: firstPositiveFloorId || firstFloorId,
      unit: null,
    });
  };

  const handleFloorChange = event => {
    onChange({ ...selected, floor: event.target.value, unit: null });
  };

  const handleUnitChange = event => {
    onChange({ ...selected, unit: event.target.value });
  };

  const filteredFloorsByBuilding = HeatmapModalUtils.filterFloorsByBuilding(siteStructure.floors, selected.building);
  const filteredUnitsByFloor = HeatmapModalUtils.filterUnitsByFloor(siteUnits, selected.floor);

  const options = {
    dimensions: getDropdownOptions(simulationDimensions.data, {
      label: item => item,
      value: item => item,
    }),
    buildings: getDropdownOptions(siteStructure.buildings, {
      label: item => `${item.street}, ${item.housenumber}`,
      value: 'id',
    }),
    floors: getDropdownOptions(filteredFloorsByBuilding, {
      label: item => `Floor ${item.floor_number}`,
      value: 'id',
    }),
    units: [
      { value: '', label: 'All' },
      ...getDropdownOptions(filteredUnitsByFloor, {
        label: item => item.client_id,
        value: 'id',
      }),
    ],
  };

  const getDimensionDisplayedValue = () => {
    const { IDLE, PENDING, PARTIAL_FULFILLED } = RequestStatus;
    if ([IDLE, PENDING, PARTIAL_FULFILLED].includes(simulationDimensions.status)) {
      return (
        <span className="dimension-loading-placeholder">
          Loading...
          <LoadingIndicator style={LOADING_STYLE} />
        </span>
      );
    }

    return selected.dimension;
  };

  return (
    <div className="dropdowns-container">
      {extraLeftFilters}

      {dropdowns.includes('dimension') && (
        <label className="heatmap-dropdown-label">
          {showDropdownLabel && (
            <p>
              <Icon style={ICON_STYLE}>poll_outline</Icon>Insights
            </p>
          )}

          <Dropdown
            value={selected.dimension || ''}
            renderValue={getDimensionDisplayedValue}
            options={options.dimensions}
            onChange={handleDimensionChange}
            className="heatmap-list"
          />
        </label>
      )}
      {dropdowns.includes('building') && (
        <label className="heatmap-dropdown-label">
          {showDropdownLabel && (
            <p>
              <Icon style={ICON_STYLE}>apartment</Icon>Building
            </p>
          )}

          <Dropdown
            value={selected.building || ''}
            options={options.buildings}
            onChange={handleBuildingChange}
            className="heatmap-list"
          />
        </label>
      )}
      {dropdowns.includes('floor') && (
        <label className="heatmap-dropdown-label">
          {showDropdownLabel && (
            <p>
              <Icon style={ICON_STYLE}>layers</Icon>Floor
            </p>
          )}

          <Dropdown
            value={selected.floor || ''}
            options={options.floors}
            onChange={handleFloorChange}
            className="heatmap-list"
          />
        </label>
      )}
      {dropdowns.includes('unit') && (
        <label className="heatmap-dropdown-label">
          {showDropdownLabel && (
            <p>
              <Icon style={ICON_STYLE}>dashboard</Icon>Unit
            </p>
          )}

          <Dropdown
            value={selected.unit || ''}
            options={options.units}
            onChange={handleUnitChange}
            className="heatmap-list"
          />
        </label>
      )}

      {extraRightFilters}
    </div>
  );
};

export default HeatmapControls;
