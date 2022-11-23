import { MapView } from '@here/harp-mapview';
import { Feature as GeoJsonFeature, Polygon } from 'geojson';
import { CameraControls } from '../components/SimulationViewer/libs/CameraControls';
import { UnitControls } from '../components/SimulationViewer/libs/UnitControls';
import Unit from './Unit';

export enum SIMULATION_MODE {
  DASHBOARD = 'dashboard',
  PLAIN = 'plain',
  SATELLITE = 'satellite',
  THREE_D_VECTOR = '3d vector',
  NORMAL = 'normal',
  HYBRID = 'hybrid',
  TRAFFIC = 'traffic',
}

export enum SIMULATION_TYPES {
  VIEW_SUN = 'view_sun',
  CONNECTIVITY = 'connectivity',
  NOISE = 'noise',
  SUN = 'sun',
}

export const DEFAULT_SIMULATION_NAME = 'buildings';

export enum SIMULATION_DISPLAYING {
  BUILDING = 10,
  HEATMAPS = 20,
  BUILDING_HEATMAPS = 30,
}

export interface SimulationViewerProps {
  buildingId?: number;
  simType: SIMULATION_MODE;
  context3dUnits?: string[]; // Unit client ids
  highlighted3dUnits?: string[]; // Unit client Ids
  colorizeByPrice?: boolean;
  currentUnits?: Unit[];
}

export type BrooksType = {
  features: { [key: string]: GeoJsonFeature<Polygon>[] };
  openings: { [key: string]: GeoJsonFeature<Polygon>[] };
  separators: { [key: string]: GeoJsonFeature<Polygon>[] };
};

export type UnitTriangle = [LatLngAltTuple, LatLngAltTuple, LatLngAltTuple];

export type ThreeDUnit = [string, UnitTriangle[]];

type SimulationValues = {
  [key: string]: number[];
};

export type LatLngAltTuple = [number, number, number];

export type MapPoints = [number, number, number]; // x,y,z projected as per the map scene

export type UnitPoints = number[];

export type LatLngHeightLiteral = { lat: number; lon: number; height: number };

export type HeatmapsType = {
  observation_points: { total: LatLngAltTuple[]; local: LatLngAltTuple[][] };
  resolution: number;
  heatmaps: SimulationValues[];
};

export type MapControlsType = {
  map: MapView;
  camera: CameraControls;
  unit: UnitControls;
};

export type RelativeCoords = { unitClientId: string; coords: MapPoints[] };

export type Positions = { centerPosition: MapPoints; camExtraDistance: number; camPosition: LatLngAltTuple };

export type RelativeCoordsResults = Positions & {
  relativeCoords: RelativeCoords[];
  relativeAlt: number;
};

export type StartCalculationMessage = {
  unitsData: unknown[];
  context3dUnits: SimulationViewerProps['context3dUnits'];
  elevation: number;
};

export type RelativeCoordsMessage = { unitProjected: RelativeCoords };
export type EndCalculationMessage = { positions: Positions; relativeAlt: number };

export type HighlightUnitsArgs = {
  mapControls: { map: MapView; unit: any };
  highlighted3dUnits: string[];
  context3dUnits: string[];
  currentUnits: Unit[];
  colorizeByPrice: boolean;
};

export type ColorizeUnitsByPriceArgs = {
  mapControls: { map: MapView; unit: any };
  currentUnits: Unit[];
};
