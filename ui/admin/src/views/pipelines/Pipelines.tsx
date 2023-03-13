import { C } from 'Common';
import { useHierarchy, useRouter } from 'Common/hooks';
import { Building, Icon } from 'archilyse-ui-components';
import { ProviderRequest } from 'Providers';
import React, { useState } from 'react';
import useSWR from 'swr';
import './pipelines.scss';
import { Pipeline as PipelineType } from 'Common/types';
import { Modal } from '@material-ui/core';
import Breadcrumb from 'Components/Breadcrumb';
import NewBuilding from './building/NewBuilding';
import EditBuilding from './building/EditBuilding';
import BuildingPipelines from './building_pipelines/BuildingPipelines';

const { PIPELINE_FOR_SITE, BUILDINGS_BY_SITE, SITE_BY_ID } = C.ENDPOINTS;

export enum BUILDING_STATUS {
  COMPLETED = 'COMPLETED',
  IN_PROGRESS = 'IN PROGRESS',
  FAILED = 'FAILED',
  NOT_STARTED = '-',
}

const SORT_ICON_COLOR = '#8C9294';

const STYLE = {
  fontSize: '20px',
  marginLeft: '5px',
  verticalAlign: 'bottom',
  color: SORT_ICON_COLOR,
};

const NAME = 'name';
const STATUS = 'status';

const ASCENDING = 1;
const DESCENDING = -1;

export const getBuildingName = (building: Building): string =>
  `Building: ${building.client_building_id || ''} (${building.street}, ${building.housenumber})`;

const getBuildingStatus = (building: Building, pipelines: PipelineType[], buildingFailed): BUILDING_STATUS => {
  if (buildingFailed === building.id) return BUILDING_STATUS.FAILED;

  const buildingPipelines = pipelines.filter(pipeline => pipeline.building_id === building.id);
  if (!buildingPipelines?.length) return BUILDING_STATUS.NOT_STARTED;

  const allPipelinesCompleted = buildingPipelines.every(
    pipeline =>
      pipeline.labelled && pipeline.classified && pipeline.splitted && pipeline.georeferenced && pipeline.units_linked
  );
  if (allPipelinesCompleted) return BUILDING_STATUS.COMPLETED;
  return BUILDING_STATUS.IN_PROGRESS;
};

const getBuildingStatusScore = (status: String): number => {
  if (status === BUILDING_STATUS.FAILED) return 1;
  else if (status === BUILDING_STATUS.IN_PROGRESS) return 2;
  else if (status === BUILDING_STATUS.COMPLETED) return 3;
  return 4;
};

type expandedBuildings = { [id: number]: boolean };

const Pipelines = () => {
  const { query } = useRouter();
  const { site_id } = query;
  const { data: buildings = [], mutate: reloadBuildings }: { data?: Building[]; mutate: () => void } = useSWR(
    BUILDINGS_BY_SITE(site_id),
    ProviderRequest.get
  );
  const { data: pipelines = [], mutate: reloadPipelines }: { data?: PipelineType[]; mutate: () => void } = useSWR(
    PIPELINE_FOR_SITE(site_id),
    ProviderRequest.get
  );
  const { data: site = {} } = useSWR(SITE_BY_ID(site_id), ProviderRequest.get);
  const [expandedBuildings, setExpandedBuldings] = useState<expandedBuildings>({}); // @TODO: Probably the should be expanded by default
  const [openAddModal, setOpenAddModal] = useState(false);
  const [buildingToEdit, setBuildingToEdit] = useState<Building>(undefined);
  const [buildingFailed, setBuildingFailed] = useState<number>();
  const hierarchy = useHierarchy();

  const [sortedBy, setSortedBy] = useState<string>(STATUS);
  const [sortOrder, setSortOrder] = useState<number>(ASCENDING);

  const onClickBuildingRow = buildingId => {
    const newExpanded = { ...expandedBuildings, [buildingId]: !expandedBuildings[buildingId] };
    setExpandedBuldings(newExpanded);
  };

  const onAdd = () => {
    setOpenAddModal(false);
    reloadBuildings();
  };

  const onEdit = () => {
    setBuildingToEdit(undefined);
    reloadBuildings();
  };

  const sortBuildingsByNameOrStatus = (a: Building, b: Building) => {
    if (sortedBy === NAME) {
      const buildingA = getBuildingName(a);
      const buildingB = getBuildingName(b);
      if (sortOrder === ASCENDING) return buildingA.localeCompare(buildingB);
      else return buildingB.localeCompare(buildingA);
    }
    const scoreA = getBuildingStatusScore(getBuildingStatus(a, pipelines, buildingFailed));
    const scoreB = getBuildingStatusScore(getBuildingStatus(b, pipelines, buildingFailed));
    return sortOrder === ASCENDING ? scoreA - scoreB : scoreB - scoreA;
  };

  const getSortArrow = sortOrder => {
    return sortOrder === DESCENDING ? <Icon style={STYLE}>south</Icon> : <Icon style={STYLE}>north</Icon>;
  };

  const sortRowsBy = field => {
    setSortedBy(field);
    sortOrder === ASCENDING ? setSortOrder(DESCENDING) : setSortOrder(ASCENDING);
  };

  // This key forces header row to re-render and adjust when we have new buildings/pipelines, otherwise the user could see a wrong header size
  const headerKey = `key-${buildings.length}-${pipelines.length}`;
  return (
    <>
      <div className="breadcrumb">
        <Breadcrumb hierarchy={hierarchy} />
      </div>

      <table className="building-list" data-testid="building-list">
        <thead className="building-list-header">
          <tr key={headerKey}>
            <th className="building-sortable-header" data-testid="building-name" onClick={() => sortRowsBy(NAME)}>
              Building
              {sortedBy === NAME ? getSortArrow(sortOrder) : null}
            </th>
            <th className="building-sortable-header" data-testid="building-status" onClick={() => sortRowsBy(STATUS)}>
              Status
              {sortedBy === STATUS ? getSortArrow(sortOrder) : null}
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {buildings.sort(sortBuildingsByNameOrStatus).map(building => {
            const buildingStatus = getBuildingStatus(building, pipelines, buildingFailed);
            const cellClass = buildingStatus.toLowerCase().replace(' ', '_');
            const hideIfNotExpanded = expandedBuildings[building.id] ? {} : { display: 'none' };
            return (
              <>
                <tr key={building.id}>
                  <td className="building-name" onClick={() => onClickBuildingRow(building.id)}>
                    <Icon>{expandedBuildings[building.id] ? 'keyboard_arrow_up' : 'keyboard_arrow_down'}</Icon>
                    {getBuildingName(building)}
                  </td>
                  <td className={cellClass}>{buildingStatus}</td>
                  <td
                    className="edit-building-button"
                    data-testid="edit-building-button"
                    onClick={() => setBuildingToEdit(building)}
                  >
                    <Icon>edit</Icon>
                  </td>
                </tr>
                <tr style={hideIfNotExpanded}>
                  {/* colspan 3 so it takes full width */}
                  <td colSpan={3}>
                    <BuildingPipelines
                      pipelines={pipelines.filter(p => p.building_id === building.id)}
                      building={building}
                      enforceMasterplan={site.enforce_masterplan}
                      reloadPipelines={reloadPipelines}
                      onFloorUpload={({ failed }) => setBuildingFailed(failed ? building.id : undefined)}
                    />
                  </td>
                </tr>
              </>
            );
          })}
          <tr>
            <td
              className="add-button add-building-button"
              data-testid="add-building-button"
              onClick={() => setOpenAddModal(true)}
            >
              <Icon style={{ marginRight: '5px', color: 'inherit' }}>add_circle</Icon>
              <p>Add...</p>
            </td>
          </tr>
        </tbody>
      </table>
      <Modal open={Boolean(buildingToEdit)} onClose={() => setBuildingToEdit(undefined)} style={C.CSS.MODAL_STYLE}>
        <div className={`crud-modal`}>
          <EditBuilding building={buildingToEdit} onEdit={onEdit} />
        </div>
      </Modal>
      <Modal open={openAddModal} onClose={() => setOpenAddModal(false)} style={C.CSS.MODAL_STYLE}>
        <div className="crud-modal">
          <NewBuilding siteId={site_id} onAdd={onAdd} />
        </div>
      </Modal>
    </>
  );
};

export default Pipelines;
