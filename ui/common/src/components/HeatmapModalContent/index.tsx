import React, { ForwardRefRenderFunction, useEffect, useState } from 'react';
import LoadingIndicator from '../LoadingIndicator';
import { RequestStatus } from '../../types/RequestStateType';
import Heatmap, { HeatmapProps } from '../Heatmap';
import { Unit } from '../../types';
import HeatmapControls from './HeatmapControls';
import useHeatmaps, { SiteStructureState } from './useHeatmaps';
import HeatmapModalUtils from './HeatmapModalUtils';
import './heatmapModalContent.scss';

const LOADING_STYLE = {
  width: 30,
  height: 30,
};

export type HeatmapsSelectedFilters = { dimension: string; building?: number; floor?: number; unit?: number };

export type HeatmapModalContentProps = {
  siteId: number;
  header: string;
  selectedByDefault: HeatmapsSelectedFilters;
  dropdowns?: ('dimension' | 'building' | 'floor' | 'unit')[];
  showDropdownLabel?: boolean;
  extraLeftFilters?: JSX.Element;
  extraRightFilters?: JSX.Element;
  footer?: JSX.Element;
  onChange?: (filters: HeatmapsSelectedFilters, siteStructure: SiteStructureState, siteUnits: Unit[]) => void;
  onClose: () => void;
} & Pick<HeatmapProps, 'showMap' | 'mapSimulationMode' | 'id'>;

const HeatmapModalContent: ForwardRefRenderFunction<any, HeatmapModalContentProps> = (
  {
    id = null,
    siteId,
    header,
    onClose,
    onChange,
    selectedByDefault,
    dropdowns = ['building', 'floor'],
    showDropdownLabel = false,
    extraLeftFilters,
    extraRightFilters,
    showMap = false,
    mapSimulationMode = null,
    footer,
  },
  _
): JSX.Element => {
  const [selected, setSelected] = useState<HeatmapsSelectedFilters>({
    building: null,
    floor: null,
    unit: null,
    ...selectedByDefault,
  });

  const { siteStructure, siteUnits, simulationDimensions } = useHeatmaps({
    siteId,
    selected,
    fetchDimensions: dropdowns.includes('dimension'),
  });

  useEffect(() => {
    if (siteStructure.status === RequestStatus.FULFILLED) {
      const firstBuilding = siteStructure.data.buildings[0].id;

      if (selectedByDefault.floor) {
        const building = HeatmapModalUtils.findBuildingByFloorId(siteStructure.data.buildings, selectedByDefault.floor);
        const floor = selectedByDefault.floor;

        setSelected({ ...selected, building: building?.id || firstBuilding, floor });
      } else {
        const floors = HeatmapModalUtils.filterFloorsByBuilding(siteStructure.data.floors, firstBuilding);
        const firstPositiveFloorId = HeatmapModalUtils.findPositiveFloorId(floors);
        const firstFloorId = floors[0].id;

        setSelected({ ...selected, building: firstBuilding, floor: firstPositiveFloorId || firstFloorId });
      }
    }
  }, [siteStructure]);

  useEffect(() => {
    setSelected(selectedByDefault);
  }, [selectedByDefault.dimension, selectedByDefault.building, selectedByDefault.floor, selectedByDefault.unit]);

  useEffect(() => {
    if (onChange) onChange(selected, siteStructure.data, siteUnits.data);
  }, [selected]);

  const renderHeatmap = () => {
    const unitIds = HeatmapModalUtils.findUnitIdsBySelected(siteUnits.data, selected);

    const floor = HeatmapModalUtils.findFloorByBuildingAndFloorId(
      siteStructure.data.floors,
      selected.building,
      selected.floor
    );
    const planId = selected.unit ? undefined : floor?.plan_id;

    return (
      <Heatmap
        key={unitIds.join(',') + String(showMap)}
        id={id}
        unitIds={unitIds}
        siteId={siteId}
        planId={planId}
        simulationName={selected.dimension}
        showMap={showMap}
        mapSimulationMode={mapSimulationMode}
      />
    );
  };

  const isLoading = siteStructure.status === RequestStatus.PENDING || siteUnits.status === RequestStatus.PENDING;

  return (
    <article className="common-modal-container heatmap-modal-container">
      <main>
        <header className="heatmap-modal-header">
          <h2>{header}</h2>
          {isLoading && <LoadingIndicator style={LOADING_STYLE} />}
        </header>

        <div className="heatmap-modal-content">
          <HeatmapControls
            siteStructure={siteStructure.data}
            siteUnits={siteUnits.data}
            simulationDimensions={simulationDimensions}
            selected={selected}
            dropdowns={dropdowns}
            showDropdownLabel={showDropdownLabel}
            extraLeftFilters={extraLeftFilters}
            extraRightFilters={extraRightFilters}
            onChange={setSelected}
          />
          <div className="heatmap-container">{renderHeatmap()}</div>
        </div>
      </main>

      <footer>
        {footer}
        <button className="default-button" onClick={onClose}>
          Close
        </button>
      </footer>
    </article>
  );
};

export default React.forwardRef(HeatmapModalContent);
