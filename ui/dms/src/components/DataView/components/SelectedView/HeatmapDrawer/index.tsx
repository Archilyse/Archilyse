import React, { useState } from 'react';
import Switch from '@material-ui/core/Switch';
import {
  DEFAULT_SIMULATION_NAME,
  downloadScreenshot,
  Heatmap,
  HeatmapModalContent,
  HeatmapProps,
  HeatmapsSelectedFilters,
  SIMULATION_MODE,
  SiteStructureState,
  Unit,
  Widget,
} from 'archilyse-ui-components';
import { useRouter } from 'Common/hooks';
import OpenHeatmapsModalButton from './OpenHeatmapsModalButton';
import './heatmapDrawer.scss';

type Props = { siteId: number } & Pick<HeatmapProps, 'unitIds' | 'planId'>;

const notFalsy = (value: any) => value !== null && value !== undefined;
const getFileName = (filters): string => {
  const dimension = filters.dimension;
  const building = [filters.building?.street, filters.building?.housenumber].filter(Boolean).join(', ');
  const floor = notFalsy(filters.floor?.floor_number) ? `Floor ${filters.floor.floor_number}` : '';
  const unit = filters.unit?.client_id || 'All units';

  return [dimension, building, floor, unit].filter(Boolean).join('-');
};

const HeatmapDrawer = ({ unitIds, planId, siteId }: Props): JSX.Element => {
  const { query } = useRouter();

  const [withContext, setWithContext] = useState(false);
  const [filters, setFilters] = useState(null);

  const handleFiltersChange = (filters: HeatmapsSelectedFilters, siteStructure: SiteStructureState, units: Unit[]) => {
    const building = siteStructure.buildings.find(building => building.id === filters.building);
    if (!building) return;
    const floor = siteStructure.floors.find(floor => floor.id === filters.floor);
    if (!floor) return;
    const unit = units.find(unit => unit.id === filters.unit);

    setFilters({
      dimension: filters.dimension,
      building,
      floor,
      unit,
    });
  };

  const handleDownload = () => {
    const filename = getFileName(filters);
    downloadScreenshot({ id: 'dms-modal-heatmap', filename, ext: 'png', width: null, height: null, style: null });
  };

  if (!unitIds || unitIds.length === 0) {
    return (
      <Widget className="heatmap-drawer" initialTab={0} tabHeaders={['Insights']}>
        <p className="no-units-data">No data available</p>
      </Widget>
    );
  }
  return (
    <Widget className="heatmap-drawer" initialTab={0} tabHeaders={['Insights']}>
      <div>
        <Heatmap
          unitIds={unitIds}
          planId={planId}
          siteId={siteId}
          simulationName={DEFAULT_SIMULATION_NAME}
          infoSize="small"
          backgroundColor={0xffffff}
        />
        <OpenHeatmapsModalButton>
          {({ onClose }) => (
            <>
              <HeatmapModalContent
                id="dms-modal-heatmap"
                header="Analysis"
                siteId={siteId}
                selectedByDefault={{ dimension: DEFAULT_SIMULATION_NAME, floor: Number(query.floor_id) }}
                onChange={handleFiltersChange}
                dropdowns={['dimension', 'building', 'floor', 'unit']}
                showDropdownLabel={true}
                showMap={withContext}
                mapSimulationMode={withContext ? SIMULATION_MODE.NORMAL : null}
                extraRightFilters={
                  <label className="heatmap-modal-toggle">
                    <small>Map</small>
                    <Switch
                      checked={withContext}
                      size={'small'}
                      className="option-switch"
                      onChange={() => setWithContext(!withContext)}
                      name="showBlocked"
                    />
                  </label>
                }
                footer={
                  <button className="primary-button" onClick={handleDownload} disabled={!filters}>
                    Download PNG
                  </button>
                }
                onClose={onClose}
              />
            </>
          )}
        </OpenHeatmapsModalButton>
      </div>
    </Widget>
  );
};

export default HeatmapDrawer;
