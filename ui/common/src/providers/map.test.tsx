import * as React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import ProviderMap from './map';

afterEach(cleanup);

const MAP_ID = 'mock-map';
const MockMap = <div id={MAP_ID}></div>;

const MOCKED_MARKERS = [
  {
    details: {
      name: 'Migros 1',
      versions: 2,
    },
    coords: [47.387054, 8.5289573],
  },
  {
    details: {
      name: 'Migros 2',
    },
    coords: [47.389944, 8.5482573],
  },
  {
    details: {
      name: 'Migros 3',
      versions: 0,
    },
    coords: [47.376165, 8.5337923],
  },
  {
    details: {
      name: 'Migros 4',
      versions: 3,
    },
    coords: [47.37913, 8.4821853],
  },
];

const isMapCreated = container => {
  const leafletMap = container.querySelector('.leaflet-container');
  return leafletMap && leafletMap.childNodes.length > 0;
};

it('Inits a map', async () => {
  const { container } = render(MockMap);
  const map = new ProviderMap();
  map.init(MAP_ID);
  expect(isMapCreated(container)).toBeTruthy();
});

it('Adds marker to the map and removes them', async () => {
  const { container } = render(MockMap);
  const map: any = new ProviderMap();
  map.init(MAP_ID);
  expect(isMapCreated(container)).toBeTruthy();
  map.addMarkers(MOCKED_MARKERS);
  // Each thing in the map is a layer: One per migros site and one more for the attribution string
  let numberOfMarkers = Object.keys(map.getInternalMapInstance()._layers).length - 1;
  expect(numberOfMarkers).toEqual(MOCKED_MARKERS.length);

  map.removeMarkers();
  numberOfMarkers = Object.keys(map.getInternalMapInstance()._layers).length - 1;
  expect(numberOfMarkers).toEqual(0);
});

it('Adds marker to the map and selects and deselect one of them', async () => {
  const { container } = render(MockMap);
  const map: any = new ProviderMap();
  map.init(MAP_ID);
  expect(isMapCreated(container)).toBeTruthy();
  // No marker selected at the beginnging
  expect(container.querySelector('.highlighted-icon')).toBeFalsy();

  // Select one marker and ensure is highlighted
  map.addMarkers(MOCKED_MARKERS);
  map.selectMarker(MOCKED_MARKERS[0]);
  expect(container.querySelector('.highlighted-icon')).toBeTruthy();

  // Deselect it and ensure no icons are highlighted
  map.clearSelectedMarker();
  expect(container.querySelector('.highlighted-icon')).toBeFalsy();
});

it('Centers the map around a group of markers', async () => {
  const EXPECTED_MARKERS_CENTER = {
    lat: 47.38305630073997,
    lng: 8.515221299999995,
  };

  const { container } = render(MockMap);
  const map: any = new ProviderMap();
  map.init(MAP_ID);
  expect(isMapCreated(container)).toBeTruthy();
  // No marker selected at the beginnging

  map.addMarkers(MOCKED_MARKERS);

  const initialCenter = map.getInternalMapInstance().getCenter();
  map.centerAroundMarkers(MOCKED_MARKERS);
  const markersCenter = map.getInternalMapInstance().getCenter();

  const centerHasChanged = initialCenter.lat !== markersCenter.lat && initialCenter.lng !== markersCenter.lng;
  expect(centerHasChanged).toEqual(true);
  expect(markersCenter).toEqual(EXPECTED_MARKERS_CENTER);
});

it('Removes the map', async () => {
  const { container } = render(MockMap);
  const map = new ProviderMap();
  map.init(MAP_ID);
  expect(isMapCreated(container)).toBeTruthy();

  map.remove();
  expect(isMapCreated(container)).toBeFalsy();
});

it('shows search bar if pass proper prop', () => {
  render(MockMap);

  const map = new ProviderMap();
  map.init(MAP_ID, { searchOptions: { search: true } });

  expect(screen.getByPlaceholderText(/enter address/i)).toBeInTheDocument();
});

it('shows draw toolbar if pass proper prop', () => {
  render(MockMap);

  const map = new ProviderMap();
  map.init(MAP_ID, { drawOptions: { draw: true } });

  expect(screen.getByText(/draw a rectangle/i)).toBeInTheDocument();
});

it('shows draw geojson if pass proper prop', () => {
  render(MockMap);

  const map = new ProviderMap();
  map.init(MAP_ID, { geojsonOptions: { draw: true, siteID: 1 } });

  expect(screen.getByText(/Remove Last Vertex/i)).toBeInTheDocument();
});
