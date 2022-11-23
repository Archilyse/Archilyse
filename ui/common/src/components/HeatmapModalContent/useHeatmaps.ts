import { useEffect, useReducer } from 'react';
import C from '../../constants';
import {
  BuildingWithFloors,
  DEFAULT_SIMULATION_NAME,
  Floor,
  RequestStateType,
  RequestStatus,
  SIMULATION_TYPES,
  SiteStructure,
  Unit,
} from '../../types';
import { ProviderRequest } from '../../providers';
import { getSimulationNames } from '../../modules';
import HeatmapModalUtils from './HeatmapModalUtils';
import { HeatmapsSelectedFilters } from '.';

export type FloorWithId = Floor & { id: number };

export type SiteStructureState = {
  buildings: BuildingWithFloors[];
  floors: FloorWithId[];
};

type SiteStructureActions =
  | { type: RequestStatus.PENDING }
  | { type: RequestStatus.FULFILLED; payload?: SiteStructure }
  | { type: RequestStatus.REJECTED; error: string };

type SiteUnitsActions =
  | { type: RequestStatus.PENDING }
  | { type: RequestStatus.FULFILLED; payload?: Unit[] }
  | { type: RequestStatus.REJECTED; error: string };

type SimulationDimensionsActions =
  | { type: 'reset' }
  | { type: RequestStatus.PENDING }
  | { type: RequestStatus.PARTIAL_FULFILLED; payload?: string[] }
  | { type: RequestStatus.FULFILLED }
  | { type: RequestStatus.REJECTED; error: string };

const initalSiteStructureState: RequestStateType<SiteStructureState> = {
  data: {
    buildings: [],
    floors: [],
  },
  status: RequestStatus.IDLE,
  error: null,
};

const initalSiteUnitsState: RequestStateType<Unit[]> = {
  data: [],
  status: RequestStatus.IDLE,
  error: null,
};
const initalSimulationDimensionsState: RequestStateType<string[]> = {
  data: [DEFAULT_SIMULATION_NAME],
  status: RequestStatus.IDLE,
  error: null,
};

const siteUnitsReducer = (state: RequestStateType<Unit[]>, action: SiteUnitsActions) => {
  switch (action.type) {
    case RequestStatus.PENDING:
      return { ...state, status: RequestStatus.PENDING };
    case RequestStatus.FULFILLED:
      return { ...state, status: RequestStatus.FULFILLED, data: action.payload };
    case RequestStatus.REJECTED:
      return { ...state, status: RequestStatus.REJECTED, error: action.error };

    default:
      return state;
  }
};

const siteStructureReducer = (state: RequestStateType<SiteStructureState>, action: SiteStructureActions) => {
  switch (action.type) {
    case RequestStatus.PENDING:
      return { ...state, status: RequestStatus.PENDING };
    case RequestStatus.FULFILLED: {
      const floors: FloorWithId[] = action.payload.buildings
        .reduce((accum: FloorWithId[], building) => {
          const buildingFloors = Object.entries(building.floors).map(([floorId, floor]) => ({
            id: Number(floorId),
            ...floor,
          }));
          return [...accum, ...buildingFloors];
        }, [])
        .sort((floorA, floorB) => floorA.floor_number - floorB.floor_number);

      const structure = {
        buildings: action.payload.buildings,
        floors,
      };

      return { ...state, status: RequestStatus.FULFILLED, data: structure };
    }
    case RequestStatus.REJECTED:
      return { ...state, status: RequestStatus.REJECTED, error: action.error };

    default:
      return state;
  }
};

const simulationDimensionsReducer = (state: RequestStateType<string[]>, action: SimulationDimensionsActions) => {
  switch (action.type) {
    case 'reset':
      return { ...initalSimulationDimensionsState, status: RequestStatus.PENDING };
    case RequestStatus.PARTIAL_FULFILLED:
      return {
        ...state,
        status: RequestStatus.PARTIAL_FULFILLED,
        data: Array.from(new Set([...state.data, ...action.payload])),
      };
    case RequestStatus.FULFILLED:
      return { ...state, status: RequestStatus.FULFILLED };
    case RequestStatus.REJECTED:
      return { ...state, status: RequestStatus.REJECTED, error: action.error };

    default:
      return state;
  }
};

type Props = {
  siteId: number;
  selected?: HeatmapsSelectedFilters;
  fetchDimensions: boolean;
};

const useHeatmaps = ({ siteId, selected, fetchDimensions }: Props) => {
  const [siteStructure, dispatchSiteStructure] = useReducer(siteStructureReducer, initalSiteStructureState);
  const [siteUnits, dispatchSiteUnits] = useReducer(siteUnitsReducer, initalSiteUnitsState);
  const [simulationDimensions, dispatchSimulationDimensions] = useReducer(
    simulationDimensionsReducer,
    initalSimulationDimensionsState
  );

  const fetchSiteStructure = async () => {
    dispatchSiteStructure({ type: RequestStatus.PENDING });
    try {
      const structure = await ProviderRequest.getCached(C.ENDPOINTS.SITE_STRUCTURE(siteId));
      dispatchSiteStructure({ type: RequestStatus.FULFILLED, payload: structure });
    } catch (error) {
      dispatchSiteStructure({ type: RequestStatus.REJECTED, error: 'Error while loading site structure' });
    }
  };

  const fetchSiteUnits = async () => {
    dispatchSiteUnits({ type: RequestStatus.PENDING });
    try {
      const structure = await ProviderRequest.getCached(C.ENDPOINTS.SITE_UNITS(siteId));
      dispatchSiteUnits({ type: RequestStatus.FULFILLED, payload: structure });
    } catch (error) {
      dispatchSiteUnits({ type: RequestStatus.REJECTED, error: 'Error while loading site units' });
    }
  };

  const fetchSimulationDimensions = async (unitIds: number[]) => {
    dispatchSimulationDimensions({ type: 'reset' });

    const requests = [SIMULATION_TYPES.VIEW_SUN, SIMULATION_TYPES.NOISE, SIMULATION_TYPES.CONNECTIVITY].reduce(
      (acc, type) => {
        const requestsPerType = unitIds
          .map(id => ProviderRequest.getCached(C.ENDPOINTS.UNIT_HEATMAPS(id, type.toUpperCase())))
          .map(promise =>
            promise
              .then(unitHeatmapsResponse => {
                const names = getSimulationNames(unitHeatmapsResponse);
                dispatchSimulationDimensions({ type: RequestStatus.PARTIAL_FULFILLED, payload: names });
              })
              .catch(() => {
                dispatchSimulationDimensions({ type: RequestStatus.PARTIAL_FULFILLED, payload: [] });
              })
          );

        return [...acc, ...requestsPerType];
      },
      []
    );

    try {
      await Promise.all(requests);
      dispatchSimulationDimensions({ type: RequestStatus.FULFILLED });
    } catch (error) {
      console.log('Error occured while loading simulation dimensions', error);
    }
  };

  useEffect(() => {
    if (siteId) Promise.all([fetchSiteStructure(), fetchSiteUnits()]);
  }, [siteId]);

  useEffect(() => {
    if (fetchDimensions && selected.floor && siteUnits.status === RequestStatus.FULFILLED) {
      const unitIds = HeatmapModalUtils.findUnitIdsBySelected(siteUnits.data, selected);

      fetchSimulationDimensions(unitIds);
    }
  }, [siteUnits, selected.floor, selected.unit, fetchDimensions]);

  return { siteStructure, siteUnits, simulationDimensions };
};

export default useHeatmaps;
