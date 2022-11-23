import * as THREE from 'three';
import { StandardGeometryKind } from '@here/harp-datasource-protocol';
import { MapAnchor, MapView } from '@here/harp-mapview';
import { GeoCoordinates } from '@here/harp-geoutils';
import C from '../../../constants';
import {
  ColorizeUnitsByPriceArgs,
  EndCalculationMessage,
  HighlightUnitsArgs,
  RelativeCoordsMessage,
  RelativeCoordsResults,
  StartCalculationMessage,
} from '../../../types';
import { CONTEXT_UNIT_OPACITY, EDGES_MATERIAL_OPACITY, UNIT_OPACITY } from './SimConstants';
// @ts-ignore
import CalculationsWorker from './UnitCalculationsWorker.ts?worker'; // This only works in chrome in development, see: https://vitejs.dev/guide/features.html#web-workers

const { DASHBOARD_3D_UNIT_COLOR, DASHBOARD_3D_EDGES_COLOR, DASHBOARD_3D_EDGES_COLOR_NO_CONTEXT, FADED_UNIT_COLOR } = C;

let unitMeshes = [];
let unitGeometries = [];

const displaySingleUnit = context3dUnits => context3dUnits.length === 1;

function cleanUnitsThreeJS(map) {
  unitGeometries.forEach(geometry => {
    geometry.dispose();
  });
  unitGeometries = [];
  unitMeshes.forEach(mesh => {
    mesh.material.dispose();
    map.scene.remove(mesh);
  });
  unitMeshes = [];

  map.mapAnchors.m_anchors.forEach(obj => {
    map.scene.remove(obj);
  });
}

export function removePreviousBuildings(map: MapView) {
  cleanUnitsThreeJS(map);
  map.mapAnchors.clear();
  map.update();
}

export function colorizeUnitsByPrice({ mapControls, currentUnits }: ColorizeUnitsByPriceArgs): void {
  if (mapControls && mapControls.unit && mapControls.map) {
    mapControls.unit.colorizeUnitsByPrice(currentUnits);
    mapControls.map.update();
  }
}

export function highlightUnits({
  mapControls,
  highlighted3dUnits,
  context3dUnits,
  currentUnits,
  colorizeByPrice,
}: HighlightUnitsArgs): void {
  if (colorizeByPrice) {
    mapControls.unit.colorizeUnitsByPrice(currentUnits);
  } else {
    mapControls.unit.restoreInitialUnitsStyle(context3dUnits);
  }
  if (mapControls && mapControls.unit && mapControls.map) {
    mapControls.unit.highlightUnits(highlighted3dUnits);
    mapControls.map.update();
  }
}

/**
 * Color and opacity for a single unit
 * Users one of the UNIT_COLORS && UNIT_OPACITY
 * @param index
 */
export function getUnitMaterial(isContextUnit: boolean): THREE.MeshPhongMaterial {
  const unitColor = isContextUnit ? DASHBOARD_3D_UNIT_COLOR : FADED_UNIT_COLOR;

  // We need to use this material in order to cast/receive shadows
  return new THREE.MeshPhongMaterial({
    color: unitColor,
    opacity: isContextUnit ? CONTEXT_UNIT_OPACITY : UNIT_OPACITY,
    transparent: true,
    side: THREE.DoubleSide,
  });
}

export function addEdgesAroundGeometry(mesh: THREE.Mesh, isContextUnit: boolean): void {
  const edgeGeometry = new THREE.EdgesGeometry(mesh.geometry);
  const edgeMaterial = new THREE.LineBasicMaterial({
    color: isContextUnit ? DASHBOARD_3D_EDGES_COLOR : DASHBOARD_3D_EDGES_COLOR_NO_CONTEXT,
    opacity: isContextUnit ? EDGES_MATERIAL_OPACITY : UNIT_OPACITY,
    transparent: true,
  });
  const wireframe = new THREE.LineSegments(edgeGeometry, edgeMaterial);
  mesh.add(wireframe);

  unitGeometries.push(edgeGeometry); // To clean it up later
}

/**
 * Creates a single unit out of a single array of "numbers" that are coordinates in this order.
 * [X1, Y1, Z1, X2, Y2, Z2, X3, Y3, Z3, ... ]
 * Coordinates should be in meters
 * @param unitRelativeCoords
 * @param index
 */
function createUnit(unitRelativeCoords: number[], isContextUnit: boolean): MapAnchor<THREE.Object3D> {
  const unit = new THREE.Object3D();
  const geometry = new THREE.BufferGeometry();
  const vertices = new Float32Array(unitRelativeCoords);
  geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
  geometry.computeVertexNormals(); // To receive light: https://stackoverflow.com/a/43574366/2904072

  const mesh = new THREE.Mesh(geometry, getUnitMaterial(isContextUnit));
  mesh.renderOrder = Number.MAX_SAFE_INTEGER;
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  addEdgesAroundGeometry(mesh, isContextUnit);

  unit.add(mesh);
  unitMeshes.push(mesh);
  unitGeometries.push(geometry);
  return unit;
}

/**
 * Created a 3d Object and positions the object in the map
 * @param map
 * @param unitRelativeCoords
 * @param index
 * @param refPosition
 */
function addUnitToMap(map: MapView, unitRelativeCoords, refPosition, isContextUnit, altPosition) {
  const unitMesh = createUnit(unitRelativeCoords, isContextUnit);
  unitMesh.anchor = new GeoCoordinates(refPosition[0], refPosition[1], altPosition);
  map.mapAnchors.add(unitMesh);
  return unitMesh;
}

async function calculateRelativeCoordsAndPositions(
  unitsData,
  context3dUnits,
  elevation
): Promise<RelativeCoordsResults> {
  return new Promise((resolve, reject) => {
    const worker = new CalculationsWorker();
    const message: StartCalculationMessage = { unitsData, context3dUnits, elevation };
    worker.postMessage(message);

    const relativeCoords = [];
    worker.onmessage = function (e) {
      if (e.data.unitProjected) {
        const { unitProjected }: RelativeCoordsMessage = e.data;
        relativeCoords.push(unitProjected);
      }
      if (e.data.positions) {
        const { positions, relativeAlt }: EndCalculationMessage = e.data;
        resolve({ relativeCoords, relativeAlt, ...positions });
        worker.terminate();
      }
    };

    worker.onerror = function (error) {
      console.error(`Error in unit calculations web worker: ${error}`);
      reject(error);
      worker.terminate();
    };
  });
}

export async function addUnits(map: MapView, unitToMeshes, unitsData, context3dUnits = [], elevation) {
  const {
    centerPosition,
    camExtraDistance,
    camPosition,
    relativeCoords,
    relativeAlt,
  } = await calculateRelativeCoordsAndPositions(unitsData, context3dUnits, elevation);

  relativeCoords.forEach(({ unitClientId, coords }) => {
    const isContextUnit = context3dUnits.length > 0 ? context3dUnits.includes(unitClientId) : true;
    const mesh = addUnitToMap(map, coords, centerPosition, isContextUnit, relativeAlt);
    if (!unitToMeshes[unitClientId]) {
      unitToMeshes[unitClientId] = [];
    }

    unitToMeshes[unitClientId].push(mesh);
  });

  if (displaySingleUnit(context3dUnits)) {
    // @TODO: Hide/display using non-deprecated methods
    map.tileGeometryManager.disableKind(StandardGeometryKind.Building);
  } else {
    map.tileGeometryManager.enableKind(StandardGeometryKind.Building);
  }
  return { camExtraDistance, camPosition };
}
