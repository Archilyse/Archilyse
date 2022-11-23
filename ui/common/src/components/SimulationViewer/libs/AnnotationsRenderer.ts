import * as THREE from 'three';
/**
 * Mathematical data to prepare the simulation and display to the user
 * @param values
 */
import { MapAnchor } from '@here/harp-mapview';
import { GeoCoordinates } from '@here/harp-geoutils';
import { LatLngTuple } from 'leaflet';
import { HeatmapsType, MapPoints } from '../../../types';

const FEATURE_WINDOW = 'WINDOW';
const FEATURE_WALL = 'WALL';
const FEATURE_DOOR = 'DOOR';
const FEATURE_ENTRANCE_DOOR = 'ENTRANCE_DOOR';
const FEATURE_TOILET = 'TOILET';
const FEATURE_RAILING = 'RAILING';

const COLOR_WHITE = 'rgb(255,255,255)';
const COLOR_GREY = 'rgb(210,210,210)';
const COLOR_BLACK = 'rgb(33,33,33)';

let annotationGeometries = [];
let annotationMeshes = [];

export function cleanThreeJSAnnotations(map) {
  annotationGeometries.forEach(geometry => {
    geometry.dispose();
  });
  annotationGeometries = [];

  annotationMeshes.forEach(mesh => {
    mesh.material.dispose();
    map.scene.remove(mesh);
  });
  annotationMeshes = [];
}

/** 
  From an array of [lat,lng] coords, returns the equivalent x,y,z points projected to the map
*/
export function getMapPointsFromCoords(map, geoJSONCoords: LatLngTuple[]): MapPoints[] {
  return geoJSONCoords.map((figureCoords: LatLngTuple) => {
    const anchor = new GeoCoordinates(...figureCoords);
    const position = new THREE.Vector3();
    map.projection.projectPoint(anchor, position);
    position.sub(map.camera.position);
    return [position.x, position.y, position.z];
  });
}

function getCameraCoords(map, zIndex): GeoCoordinates {
  const geoPosition = map.projection.unprojectPoint(map.camera.position);
  const cameraGeoCoordinates = [geoPosition.latitude, geoPosition.longitude, 0];
  return new GeoCoordinates(cameraGeoCoordinates[0], cameraGeoCoordinates[1], zIndex);
}

/**
 * Get's a swiss topo geoJson to be rendered using the given material and zIndex
 * @param map
 * @param geoJson
 * @param material
 * @param zIndex
 * @param referenceCenter
 * @param transformationMatrix
 */
export function drawGeoJson(map, geoJson, material, zIndex, options) {
  const outerCoordinates = 0;

  const geoJSONCoords = geoJson.geometry.coordinates[outerCoordinates];

  // Get the projected map x,y,z points of the perimeter/brooks based on the lat/lng
  const perimeterPoints = getMapPointsFromCoords(map, geoJSONCoords);

  // We build a polygon based on those points
  const newPolygon = drawPolygon(perimeterPoints, material, options);

  // And we place in the lat, lng of the camera
  newPolygon.anchor = getCameraCoords(map, zIndex);

  map.mapAnchors.add(newPolygon);
  map.update();
}

/**
 * Generates a polygon to be added to the map
 * @param perimeterMapRelative
 * @param material
 */
export function drawPolygon(perimeterMapRelative, material, { drawEdges }): MapAnchor<THREE.Object3D> {
  const polygon = new THREE.Object3D();
  const polygonShape = new THREE.Shape();

  polygonShape.moveTo(perimeterMapRelative[0][0], perimeterMapRelative[0][1]);
  for (let i = 1; i < perimeterMapRelative.length; i += 1) {
    // Back to the first point
    const p = perimeterMapRelative[i]; // === perimeterMapRelative.length ? 0 : i];
    polygonShape.lineTo(p[0], p[1]);
  }

  const extrudeSettings = { depth: 0.001, steps: 2, bevelEnabled: false };
  const geometry = new THREE.ExtrudeBufferGeometry(polygonShape, extrudeSettings);

  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = Number.MAX_SAFE_INTEGER;
  polygon.add(mesh);

  if (drawEdges) {
    const edges = new THREE.EdgesGeometry(geometry);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000 }));
    polygon.add(line);
    annotationGeometries.push(geometry);
  }
  annotationMeshes.push(mesh);
  annotationGeometries.push(geometry);

  return polygon;
}

export function drawGeoJsonArray(map, geoJsonArray, material, zIndex, options) {
  if (geoJsonArray) {
    geoJsonArray.forEach(geoJson => {
      drawGeoJson(map, geoJson, material, zIndex, options);
    });
  }
}

/**
 * Gets a material and a zIndex for each feature name
 * @param featureName
 */
export function getFeatureColor(featureName) {
  let material;
  let zIndex;

  if (featureName === FEATURE_WINDOW) {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_WHITE,
    });
    zIndex = 0.07;
  } else if (featureName === FEATURE_WALL) {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_BLACK,
    });
    zIndex = 0.05;
  } else if (featureName === FEATURE_DOOR || featureName === FEATURE_ENTRANCE_DOOR) {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_WHITE,
    });
    zIndex = 0.06;
  } else if (featureName === FEATURE_TOILET) {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_WHITE,
    });
    zIndex = 0.01;
  } else if (featureName === FEATURE_RAILING) {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_GREY,
    });
    zIndex = 0.01;
  } else {
    material = new THREE.MeshBasicMaterial({
      color: COLOR_WHITE,
    });
    zIndex = 0.02;
  }

  return { material, zIndex };
}

/**
 * Draws all the annotations contained with color and zIndex based on the annotation name.
 * @param map
 * @param annotations
 * @param referenceCenter
 * @param transformationMatrix
 */
export function drawAnnotations(map, annotations, options = { drawEdges: false }) {
  Object.keys(annotations || {}).forEach(annotationName => {
    const { material, zIndex } = getFeatureColor(annotationName);
    drawGeoJsonArray(map, annotations[annotationName], material, zIndex, options);
  });
}

export function extractSimulations(heatmaps = []): HeatmapsType {
  const finalHexagons: HeatmapsType = { observation_points: { total: [], local: [] }, resolution: 0.25, heatmaps: [] };

  heatmaps.forEach(heatmap => {
    if (heatmap) {
      const { observation_points, resolution, ...simulations } = heatmap;

      finalHexagons.heatmaps.push(simulations);

      finalHexagons.observation_points.local.push(observation_points);
      finalHexagons.observation_points.total.push(...observation_points);

      if (resolution) finalHexagons.resolution = resolution;
    }
  });

  return finalHexagons;
}

export function mergeGroup(finalBrooks, brooks, groupName) {
  if (brooks.layout?.[groupName]) {
    Object.keys(brooks.layout[groupName]).forEach(key => {
      if (!finalBrooks[groupName][key]) {
        finalBrooks[groupName][key] = [];
      }
      finalBrooks[groupName][key].push(...brooks.layout[groupName][key]);
    });
  }
}
