import * as THREE from 'three';
/**
 * Mathematical data to prepare the simulation and display to the user
 * @param values
 */
import { MapAnchor, MapView } from '@here/harp-mapview';
import * as d3 from 'd3';
import { GeoCoordinates } from '@here/harp-geoutils';
import { LatLngTuple } from 'leaflet';
import { LatLngAltTuple } from '../../../types';
import { colors } from './SimConstants';

let geometries = [];
let meshes = [];

/**
 * Given the color array maps from min to max to a color
 * Returns the transforming function
 * @param min
 * @param max
 * @returns function
 */
export function calculateDomain(min, max) {
  // Create a domain that divides the range of values
  const domain = colors.map((c, i) => min + (i / (colors.length - 1)) * (max - min));
  // Create a scale that allows us to convert our values to a colour
  return d3.scaleLinear().domain(domain).range(colors);
}

export function cleanHeatmap(map: MapView) {
  geometries.forEach(geometry => {
    geometry.dispose();
  });
  geometries = [];
  meshes.forEach(mesh => {
    mesh.material.dispose();
    map.mapAnchors.remove(mesh);
  });
  meshes = [];

  map.update();
}

export function cleanBrooks(map: MapView) {
  map.mapAnchors.clear();
  map.update();
}

function cleanThreeJS(map) {
  geometries.forEach(geometry => {
    geometry.dispose();
  });
  geometries = [];
  meshes.forEach(mesh => {
    mesh.material.dispose();
    map.scene.remove(mesh);
  });
  meshes = [];

  map.mapAnchors.m_anchors.forEach(obj => {
    map.scene.remove(obj);
  });
}

export function removePreviousSims(map: any) {
  cleanThreeJS(map);
  map.mapAnchors.clear();
  map.update();
}

export function emptyElement(): MapAnchor<THREE.Object3D> {
  return new THREE.Object3D();
}

/**
 * Calculates the transformation matrix for a given coordinate.
 * @param coor
 * @param coorRef
 */
export function calculateRelative(coor, coorRef) {
  return [coor.x - coorRef.x, coor.y - coorRef.y, coor.z - coorRef.z];
}

export function calculate3dScale(
  map: MapView,
  centerCoordinates: LatLngTuple | LatLngAltTuple,
  [x, y] = [0.675, 1.475]
): [number[], number[], number[]] {
  const [lat, lng, alt = 0] = centerCoordinates;
  // these coefficients set the proper simulation size (width, length, height)
  // don't ask why these specific numbers, they just work and were tested on multiple buildings
  const [latCoef, lngCoef, altCoef] = [x, y, 1.8];

  const center: LatLngAltTuple = [lat, lng, alt];
  const center_100_0: LatLngAltTuple = [lat + latCoef, lng, 0];
  const center_0_100: LatLngAltTuple = [lat, lng + lngCoef, 0];
  const center_0_0_100: LatLngAltTuple = [lat, lng, alt + altCoef];

  const geoCoor = new GeoCoordinates(...center);
  const geoCoor_1_0_0 = new GeoCoordinates(...center_100_0);
  const geoCoor_0_1_0 = new GeoCoordinates(...center_0_100);
  const geoCoor_0_0_1 = new GeoCoordinates(...center_0_0_100);

  const ref = emptyElement();
  const refX = emptyElement();
  const refY = emptyElement();
  const refZ = emptyElement();

  ref.anchor = geoCoor;
  refX.anchor = geoCoor_1_0_0;
  refY.anchor = geoCoor_0_1_0;
  refZ.anchor = geoCoor_0_0_1;

  map.mapAnchors.add(ref);
  map.mapAnchors.add(refX);
  map.mapAnchors.add(refY);
  map.mapAnchors.add(refZ);

  const projection = map.projection.projectPoint(geoCoor);
  const projectionX = map.projection.projectPoint(geoCoor_0_1_0);
  const projectionY = map.projection.projectPoint(geoCoor_1_0_0);
  const projectionZ = map.projection.projectPoint(geoCoor_0_0_1);

  return [
    calculateRelative(projectionX, projection), // X
    calculateRelative(projectionY, projection), // Y
    calculateRelative(projectionZ, projection), // Z
  ];
}

export function computeHexagonColors(observation_points, values, valueToColor): Float32Array {
  const _color = new THREE.Color();
  const hexagonColors = new Float32Array(observation_points.length * 3); // * 3 as we are storing RGB colors

  for (let i = 0; i < observation_points.length; i++) {
    const value = values[i];
    const stringRGBColor = valueToColor(value);
    _color.setStyle(stringRGBColor);
    _color.toArray(hexagonColors, i * 3);
  }
  return hexagonColors;
}

/*
 * This method will define where every hexagon must be located by converting
 *  its lat & long coordinates to x,y,z in the 3d scene, following how
 *  harp.gl does the same:  https://github.com/heremaps/harp.gl/blob/master/%40here/harp-mapview/lib/MapView.ts#L634
 */
function setUpMatrix(matrix, coords: LatLngTuple, map, maxtrixParameters) {
  const { position, quaternion, scale, rotation } = maxtrixParameters;

  // Convert the point to x,y,z
  const anchor = new GeoCoordinates(...coords);
  map.projection.projectPoint(anchor, position);

  // Get the point in the current scene taking into the account the camera position
  position.sub(map.camera.position);
  position.z = 0;
  quaternion.setFromEuler(rotation);
  scale.x = scale.y = scale.z = 1;
  matrix.compose(position, quaternion, scale);
}

function createInstancedMesh(
  hexagonGeometry,
  material,
  observation_points,
  map,
  cameraGeoCoordinates: LatLngAltTuple
): THREE.InstancedMesh {
  const matrix = new THREE.Matrix4();
  const mesh: any = new THREE.InstancedMesh(hexagonGeometry, material, observation_points.length);

  const matrixParameters = {
    position: new THREE.Vector3(),
    rotation: new THREE.Euler(),
    quaternion: new THREE.Quaternion(),
    scale: new THREE.Vector3(),
  };

  observation_points.forEach((point, index) => {
    setUpMatrix(matrix, point, map, matrixParameters);
    mesh.setMatrixAt(index, matrix);
  });

  mesh.renderOrder = Number.MAX_SAFE_INTEGER;

  // This will tell the map to add the mesh in the same lat/lng as the camera
  mesh.anchor = new GeoCoordinates(...cameraGeoCoordinates);
  return mesh;
}

/**
 * Draw a single simulation in the map for the calculated observation_points
 *
 * This will:
 *  1. Create a single geometry object, shared for all the hexagons
 *  2. Create an array of colors for every hexagon, depending on its value
 *  3. Create an instanced mesh, using a single material & geometry, and with a matrix that defines the position of every hexagon.
 *  4. Add the instanced mesh to the map
 *
 * @param map
 * @param values,
 * @param observation_points
 * @param valueToColor
 * @param rotationToNorth
 * @param cameraGeoCoordinates
 * @param hexagonRadius
 */
export function drawHexagons(
  map: MapView,
  values,
  observation_points,
  valueToColor,
  rotationToNorth: number,
  cameraGeoCoordinates,
  hexagonRadius = 0.2
) {
  const hexagonGeometry = getHexagonShape(hexagonRadius, rotationToNorth);

  const hexagonColors = computeHexagonColors(observation_points, values, valueToColor);
  hexagonGeometry.setAttribute('color', new THREE.InstancedBufferAttribute(hexagonColors, 3));

  const material = new THREE.MeshBasicMaterial({ vertexColors: true });

  const mesh: any = createInstancedMesh(hexagonGeometry, material, observation_points, map, cameraGeoCoordinates);
  map.mapAnchors.add(mesh);

  meshes.push(mesh);
  geometries.push(hexagonGeometry);
}

/**
 * Rotates the coordinates from the 0,0 coordinate X degrees.
 * @param xPos
 * @param yPos
 * @param angleDegrees
 */
export function getRotatedPoint(xPos: number, yPos: number, angleDegrees: number) {
  const angleRadians = (angleDegrees * Math.PI) / 180;
  const cos = Math.cos(angleRadians);
  const sin = Math.sin(angleRadians);
  return {
    x: xPos * cos + yPos * sin,
    y: yPos * cos - xPos * sin,
  };
}

/**
 * Returns an extruded hexagon for the given radious
 * @param radius
 * @param rotationToNorth
 */
export function getHexagonShape(radius: number, rotationToNorth = 0): THREE.ExtrudeBufferGeometry {
  const sin30 = 0.5; // 0.5 = sin 30 deg
  const cos30 = 0.866; // 0.866 = cos 30 deg

  const deltaY = radius * sin30;
  const deltaX = radius * cos30;

  // Commented each point as the position in the clock
  const hexShape = new THREE.Shape();

  // We create and rotate the hexagon to the proper orientation
  const points = [
    [0, -radius], // 12h;
    [-deltaX, -deltaY], // 10h;
    [-deltaX, deltaY], //  8h;
    [0, radius], //  6h;
    [deltaX, deltaY], //  4h;
    [deltaX, -deltaY], //  2h;
    [0, -radius], //  12h;
  ].map(point => getRotatedPoint(point[0], point[1], rotationToNorth));

  const firstPoint = points[0];
  hexShape.moveTo(firstPoint.x, firstPoint.y);

  for (let i = 1; i < points.length; i += 1) {
    const point = points[i];
    hexShape.lineTo(point.x, point.y);
  }

  const extrudeSettings = { depth: 0.001, steps: 2, bevelEnabled: false };
  return new THREE.ExtrudeBufferGeometry(hexShape, extrudeSettings);
}
