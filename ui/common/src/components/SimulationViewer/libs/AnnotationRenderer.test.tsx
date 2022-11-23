import * as THREE from 'three';

import { LatLngTuple } from 'leaflet';
import { MapPoints } from '../../../types';
import {
  drawAnnotations,
  drawGeoJson,
  drawGeoJsonArray,
  drawPolygon,
  extractSimulations,
  getFeatureColor,
  getMapPointsFromCoords,
  mergeGroup,
} from './AnnotationsRenderer';

// Mocks taken from calibrator 401, unit 80647
const MOCK_CAMERA_POSITION = new THREE.Vector3(20989901.739434615, 26047527.7852657, 20.837529213153516);
const MOCK_PROJECTED_POINT = { x: 20989908.55307581, y: 26047523.60527753, z: 0 };

let numAnchors = 0;
const mapMock = {
  projection: {
    projectPoint: (anchor, pos) => pos.set(MOCK_PROJECTED_POINT.x, MOCK_PROJECTED_POINT.y, MOCK_PROJECTED_POINT.z),
    unprojectPoint: () => ({ latitude: 1, longitude: 1 }),
  },
  camera: { position: MOCK_CAMERA_POSITION },
  removeDataSource: mapSource => {},
  setUpDataSource: mapSource => {},
  addDataSource: mapSource => {},
  update: () => {},
  mapAnchors: {
    add: () => {
      numAnchors += 1;
    },
  },
};

const annotationsMock = {
  DOORS: [
    {
      geometry: {
        type: 'polygon',
        coordinates: [
          [
            [1, 2],
            [2, 2],
          ],
        ],
      },
    },
  ],
  WINDOWS: [
    {
      geometry: {
        type: 'polygon',
        coordinates: [
          [
            [1, 2],
            [2, 2],
          ],
        ],
      },
    },
  ],
};

it('should draw a geoJson data as a wall', () => {
  const { material, zIndex } = getFeatureColor('WALL');
  expect(zIndex).toBe(0.05);
  expect(material.color.r).toBeCloseTo(0.13, 2);
  expect(material.color.g).toBeCloseTo(0.13, 2);
  expect(material.color.g).toBeCloseTo(0.13, 2);

  const geoJson = {
    geometry: {
      type: 'polygon',
      coordinates: [
        [
          [1, 2],
          [2, 2],
        ],
      ],
    },
  };

  const originalAnchors = numAnchors;
  drawGeoJson(mapMock, geoJson, material, zIndex, { drawEdges: false });
  expect(numAnchors).toBe(originalAnchors + 1);
});

it('should draw a relative polygon as fake door', () => {
  const { material, zIndex } = getFeatureColor('DOOR');
  expect(zIndex).toBe(0.06);
  expect(material.color.r).toBe(1);
  expect(material.color.g).toBe(1);
  expect(material.color.g).toBe(1);

  const perimeterMapRelative = [
    [1, 2],
    [2, 2],
  ];
  const polygon = drawPolygon(perimeterMapRelative, material, { drawEdges: false });
  expect(polygon).toBeDefined();
  expect(polygon.uuid).toBeDefined();
});

it('should draw a relative polygon as a toilet with edges', () => {
  const { material, zIndex } = getFeatureColor('TOILET');
  expect(zIndex).toBe(0.01);
  expect(material.color.r).toBe(1);
  expect(material.color.g).toBe(1);
  expect(material.color.g).toBe(1);

  const perimeterMapRelative = [
    [1, 2],
    [2, 2],
  ];
  const polygon = drawPolygon(perimeterMapRelative, material, { drawEdges: true });
  expect(polygon).toBeDefined();
  expect(polygon.uuid).toBeDefined();
});

it('should draw an array of fake windows', () => {
  const { material, zIndex } = getFeatureColor('WINDOW');
  expect(zIndex).toBe(0.07);
  expect(material.color.r).toBe(1);
  expect(material.color.g).toBe(1);
  expect(material.color.g).toBe(1);

  const geoJsonArray = [
    {
      geometry: {
        type: 'polygon',
        coordinates: [
          [
            [1, 2],
            [2, 2],
          ],
          [
            [1, 2],
            [2, 2],
          ],
        ],
      },
    },
    {
      geometry: {
        type: 'polygon',
        coordinates: [
          [
            [1, 2],
            [2, 2],
          ],
        ],
      },
    },
  ];

  const originalAnchors = numAnchors;
  drawGeoJsonArray(mapMock, geoJsonArray, material, zIndex, { drawEdges: false });
  expect(numAnchors).toBe(originalAnchors + 2);
});

it('should get entrance_door colors and index properly', () => {
  const { material, zIndex } = getFeatureColor('ENTRANCE_DOOR');
  expect(zIndex).toBe(0.06);
  expect(material.color.r).toBe(1);
  expect(material.color.g).toBe(1);
  expect(material.color.g).toBe(1);
});

it('should get toilet colors and index properly', () => {
  const { material, zIndex } = getFeatureColor('TOILET');
  expect(zIndex).toBe(0.01);
  expect(material.color.r).toBe(1);
  expect(material.color.g).toBe(1);
  expect(material.color.g).toBe(1);
});

it('should get reiling colors and index properly', () => {
  const { material, zIndex } = getFeatureColor('RAILING');
  expect(zIndex).toBe(0.01);
  expect(material.color.r).toBe(0.8235294117647058);
  expect(material.color.g).toBe(0.8235294117647058);
  expect(material.color.g).toBe(0.8235294117647058);
});

it('should merge the floor hexagons from a floor', () => {
  const heatmaps = [
    // Fake values for floor 1
    {
      green: [1, 2],
      site: [4],
      observation_points: [0.4, 0.2, 0.8],
      resolution: 0.25,
    },
    // Fake values for floor 2
    {
      green: [6, 7, 8],
      site: [2],
      building: [3, 4],
      observation_points: [1.3, 1.2, 1.1],
      resolution: 0.25,
    },
  ];

  const result = extractSimulations(heatmaps);

  expect(result.resolution).toBe(0.25);
  expect(result.observation_points).toEqual({
    total: [0.4, 0.2, 0.8, 1.3, 1.2, 1.1],
    local: [
      [0.4, 0.2, 0.8],
      [1.3, 1.2, 1.1],
    ],
  });
  expect(result.heatmaps).toEqual([
    { green: [1, 2], site: [4] },
    { green: [6, 7, 8], site: [2], building: [3, 4] },
  ]);
});

it('should merge a group of annotations ', () => {
  const finalBrooks = {
    features: {},
    openings: {},
    separators: {},
    unit_client_id: null,
    unit_id: null,
  };

  const brooksMocks = {
    layout: {
      features: {
        ...annotationsMock,
      },
    },
  };

  mergeGroup(finalBrooks, brooksMocks, 'features');

  expect(Object.keys(finalBrooks.features).length).toBe(2);
  expect(Object.keys(finalBrooks.features['DOORS']).length).toBe(1);
  expect(Object.keys(finalBrooks.features['WINDOWS']).length).toBe(1);

  // Adding the elements again
  mergeGroup(finalBrooks, brooksMocks, 'features');

  // Double the features
  expect(Object.keys(finalBrooks.features).length).toBe(2);
  expect(Object.keys(finalBrooks.features['DOORS']).length).toBe(2);
  expect(Object.keys(finalBrooks.features['WINDOWS']).length).toBe(2);
});

it('should draw a set of annotations', () => {
  const originalAnchors = numAnchors;
  drawAnnotations(mapMock, annotationsMock);
  expect(numAnchors).toBe(originalAnchors + 2);
});

it('should get local map points from an array of lat lon coordinates', () => {
  const MOCK_LAT_LON_COORDS: LatLngTuple[] = [
    [47.414645738011686, 8.555499584347796],
    [47.414645407685015, 8.55555869620236],
    [47.41464368663953, 8.555558675327273],
    [47.414644016966214, 8.55549956347463],
    [47.414645738011686, 8.555499584347796],
  ];

  const EXPECTED_OUTPUT = [
    [6.81364119425416, -4.179988168179989, -20.837529213153516],
    [6.81364119425416, -4.179988168179989, -20.837529213153516],
    [6.81364119425416, -4.179988168179989, -20.837529213153516],
    [6.81364119425416, -4.179988168179989, -20.837529213153516],
    [6.81364119425416, -4.179988168179989, -20.837529213153516],
  ];

  const mapPoints: MapPoints[] = getMapPointsFromCoords(mapMock, MOCK_LAT_LON_COORDS);

  expect(mapPoints).toEqual(EXPECTED_OUTPUT);
});
