import React, { useEffect, useState } from 'react';
import {
  getSimulationNames,
  RequestStateType,
  RequestStatus,
  SIMULATION_MODE,
  SIMULATION_TYPES,
  SimulationViewer,
} from 'archilyse-ui-components';
import { useLocation, useParams } from 'react-router-dom';
import ProviderRequest from '../../providers/request';
import { C } from '../../common';
import { QA_GROUPS, QA_MODES, SiteSimulationValidation } from '../../common/types';
import Controls from './Controls';
import Heatmaps from './Heatmaps';
import './qa.scss';

export type CurrentSelection = {
  buildingId: number;
  unitId?: number;
  floorId?: number;
  simulationName?: string;
  simulationGroup?: QA_GROUPS;
  simulationMode: QA_MODES;
};

export type SimulationValidation = { id: number; label: string; errors: string[] };

type SiteStructure = {
  buildings: any[];
  floors: any[];
  units: any[];
  simulationValidation: SimulationValidation[];
};

type Options = {
  simulations: string[];
  buildings: any[];
  floors: any[];
  units: any[];
  groups: QA_GROUPS[];
};

const DEFAULT_VIEW_SUN_SIMULATION = 'buildings';

const initialSimulations: RequestStateType<string[]> = {
  data: undefined,
  status: RequestStatus.IDLE,
  error: null,
};

const SIMULATION_TYPE_BY_QA_GROUP: Record<QA_GROUPS, SIMULATION_TYPES> = {
  [QA_GROUPS.VIEW]: SIMULATION_TYPES.VIEW_SUN,
  [QA_GROUPS.SUN]: SIMULATION_TYPES.VIEW_SUN,
  [QA_GROUPS.CONNECTIVITY]: SIMULATION_TYPES.CONNECTIVITY,
  [QA_GROUPS.NOISE]: SIMULATION_TYPES.NOISE,
};

const getSiteFloors = structureData => {
  return structureData.buildings.reduce((accum, building) => {
    const buildingFloors = Object.entries(building.floors).map(([floorId, floor]: any) => ({
      id: floorId,
      ...floor,
    }));
    return [...accum, ...buildingFloors];
  }, []);
};

const getAvailableFloors = (currentSelection, siteStructure) => {
  return currentSelection?.buildingId
    ? siteStructure?.floors.filter(f => f.building_id == currentSelection?.buildingId)
    : siteStructure?.floors;
};

const getAvailableUnits = (currentSelection, siteStructure) => {
  const units = siteStructure?.units || [];

  return currentSelection?.floorId ? units.filter(u => u.floor_id == currentSelection?.floorId) : units;
};

const formatSimulationValidation = (simulationValidation: SiteSimulationValidation, units) => {
  if (!simulationValidation) return [];

  return Object.keys(simulationValidation).map(
    (unitId: string): SimulationValidation => {
      const unit = units.find(unit => unit.id === Number(unitId));

      return {
        id: Number(unitId),
        label: unit.client_id,
        errors: simulationValidation[unitId],
      };
    }
  );
};

const fetchSiteStructure = siteId => ProviderRequest.get(C.ENDPOINTS.SITE_STRUCTURE(siteId));
const fetchSiteUnits = siteId => ProviderRequest.get(C.ENDPOINTS.SITE_UNITS(siteId));
const fetchSite = siteId => ProviderRequest.get(C.ENDPOINTS.SITE(siteId));
const fetchSimulationValidation = siteId => ProviderRequest.get(C.ENDPOINTS.SITE_SIM_VALIDATION(siteId));

const fetchInitialData = async siteId => {
  const requests = [
    fetchSiteStructure(siteId),
    fetchSiteUnits(siteId),
    fetchSite(siteId),
    fetchSimulationValidation(siteId),
  ].map(request => request.catch(error => console.error(error)));
  const [structureData, units, site, simulationValidation] = await Promise.all(requests);

  const siteStructure: SiteStructure = {
    buildings: structureData.buildings,
    floors: getSiteFloors(structureData),
    units,
    simulationValidation: formatSimulationValidation(simulationValidation, units),
  };

  const firstFloor = Object.keys(siteStructure.buildings[0].floors)[0];
  const currentSelection = {
    buildingId: siteStructure.buildings[0].id,
    floorId: Number(firstFloor),
    simulationName: DEFAULT_VIEW_SUN_SIMULATION,
    simulationGroup: Object.values(QA_GROUPS)[0],
    simulationMode: QA_MODES.GROUP,
  };

  return { siteStructure, currentSelection, site };
};

const QA = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const { search: query } = useLocation();

  const queryValue = query.split('?background=')[1]?.toUpperCase() || '';
  const threeDBackground = SIMULATION_MODE[queryValue] || SIMULATION_MODE.THREE_D_VECTOR;

  const [currentSelection, setCurrentSelection] = useState<CurrentSelection | undefined>();
  const [siteStructure, setSiteStructure] = useState<SiteStructure | undefined>();
  const [site, setSite] = useState<any>();
  const [simulations, setSimulations] = useState<RequestStateType<string[]>>(initialSimulations);
  const [savingNotes, setSavingNotes] = useState<boolean>(false);
  const [validatingHeatmaps, setValidatingHeatmaps] = useState<boolean>(false);

  const loadInitialData = async () => {
    const { siteStructure, currentSelection, site } = await fetchInitialData(siteId);
    setSiteStructure(siteStructure);
    setCurrentSelection(currentSelection);
    setSite(site);

    if (siteStructure.units) {
      const [firstUnit] = siteStructure.units;
      const requests = Object.values(SIMULATION_TYPES).map(type => loadMoreSimulations(type, [firstUnit.id]));

      Promise.all(requests);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (currentSelection) {
      const type = SIMULATION_TYPE_BY_QA_GROUP[currentSelection.simulationGroup];

      const unitIds = currentSelection.unitId
        ? [currentSelection.unitId]
        : getAvailableUnits(currentSelection, siteStructure).map(unit => unit.id);

      loadMoreSimulations(type, unitIds);
    }
  }, [currentSelection]);

  useEffect(() => {
    document.title = 'QA | Archilyse';
  }, []);

  const loadMoreSimulations = async (type: SIMULATION_TYPES, unitIds: number[]) => {
    const requests = unitIds
      .map(id => ProviderRequest.getCached(C.ENDPOINTS.UNIT_HEATMAPS(id, type.toUpperCase())))
      .map(promise =>
        promise.then(unitHeatmapsResponse => {
          setSimulations(oldSimulations => {
            const names = getSimulationNames(unitHeatmapsResponse);
            const newSimulations = Array.from(new Set([...oldSimulations.data, ...names]));

            return { ...oldSimulations, data: newSimulations, status: RequestStatus.FULFILLED };
          });
        })
      );

    setSimulations({ ...simulations, status: RequestStatus.PENDING, data: [] });
    try {
      await Promise.all(requests);
    } catch (error) {
      let message = 'Error occured while loading heatmaps';
      if (error.response?.status === 404) {
        message = `There are no simulations with ${type.toUpperCase()} type`;
      }

      setSimulations({ status: RequestStatus.REJECTED, data: [], error: message });
    }
  };

  const updateSelection = (key, value) => {
    setCurrentSelection({ ...currentSelection, [key]: value });
    setSimulations({ ...simulations, data: [] });
  };

  const onValidateHeatmaps = async () => {
    setValidatingHeatmaps(true);
    const site = await ProviderRequest.put(C.ENDPOINTS.SITE(siteId), { heatmaps_qa_complete: true });
    setSite(site);
    setValidatingHeatmaps(false);
  };

  const onSaveNotes = async notes => {
    setSavingNotes(true);
    const site = await ProviderRequest.put(C.ENDPOINTS.SITE(siteId), { validation_notes: notes });
    setSite(site);
    setSavingNotes(false);
  };

  const options: Options = {
    simulations: simulations.data,
    buildings: siteStructure?.buildings,
    floors: getAvailableFloors(currentSelection, siteStructure),
    units: getAvailableUnits(currentSelection, siteStructure),
    groups: Object.values(QA_GROUPS),
  };

  const handlers = {
    onSelectSimulationName: event => updateSelection('simulationName', event.target.value),
    onSelectSimulationGroup: event => updateSelection('simulationGroup', event.target.value),
    onSelectSimulationMode: event => updateSelection('simulationMode', event.target.value),
    onSelectBuilding: event => {
      const selectedBuildingId = Number(event.target.value);
      const floors = getAvailableFloors({ buildingId: selectedBuildingId }, siteStructure);
      const firstFloorId = floors?.[0].id;

      setCurrentSelection({
        ...currentSelection,
        buildingId: selectedBuildingId,
        floorId: firstFloorId || null,
        unitId: null,
      });
      setSimulations({ ...simulations, data: [] });
    },
    onSelectFloor: event => {
      setCurrentSelection({ ...currentSelection, floorId: Number(event.target.value), unitId: null });
      setSimulations({ ...simulations, data: [] });
    },
    onSelectUnit: event => {
      if (!event.target.value) {
        setCurrentSelection({
          ...currentSelection,
          unitId: null,
        });
      } else {
        const unit = siteStructure.units.find(unit => unit.id === Number(event.target.value));
        const floor = siteStructure.floors.find(floor => Number(floor.id) === unit.floor_id);

        setCurrentSelection({
          ...currentSelection,
          buildingId: floor.building_id,
          floorId: floor.id,
          unitId: unit.id,
        });
      }

      setSimulations({ ...simulations, data: [] });
    },
    onSaveNotes: onSaveNotes,
    onValidateHeatmaps: onValidateHeatmaps,
  };

  const hasError = simulations.status === RequestStatus.REJECTED;
  const errorMessage = simulations.error || 'Error occured';

  return (
    <div className="qa">
      <div className="controls-drawer">
        <Controls
          options={options}
          handlers={handlers}
          currentSelection={currentSelection}
          savingNotes={savingNotes}
          validatingHeatmaps={validatingHeatmaps}
          validationNotes={site?.validation_notes}
          isValidated={site?.heatmaps_qa_complete}
          simulationValidation={siteStructure?.simulationValidation}
        />
      </div>
      <main className="main-content">
        <h2 className="site-title">{site?.name}</h2>
        <div className="threed-viewer">
          <SimulationViewer
            simType={threeDBackground}
            buildingId={currentSelection?.buildingId}
            highlighted3dUnits={options?.units?.map(unit => unit.unit_client_id)}
          />
        </div>
        <div className="heatmaps">
          {hasError && <p>{errorMessage}</p>}
          <Heatmaps
            currentSelection={currentSelection}
            siteId={siteId}
            floors={options.floors}
            units={options.units}
            simulations={options.simulations}
          />
        </div>
      </main>
    </div>
  );
};

export default QA;
