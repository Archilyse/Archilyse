import { LatLngTuple } from 'leaflet';
import { GeoJsonObject } from 'geojson';

export type MarkerType = {
  details: {
    name: string;
    versions?: number;
  };
  coords: LatLngTuple;
};

export type GeoJsonOptions = {
  draw: boolean;
  initialGeoJson?: GeoJsonObject;
  sitePlans?: GeoJsonObject;
  siteID: number;
  onSaved?: (...args) => void;
  onError?: (...args) => void;
};
