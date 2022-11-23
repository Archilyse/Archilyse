import * as THREE from 'three';
import { GeoCoordinates, mercatorProjection } from '@here/harp-geoutils';
import { LatLngAltTuple, MapPoints, UnitPoints } from '../../..';
import { StartCalculationMessage, ThreeDUnit, UnitTriangle } from '../../../types';

const Z_FACTOR = 1.53;

const displaySingleUnit = context3dUnits => context3dUnits.length === 1;

/**
 * Out of all given coordinates returns the center of the building
 * And the point where the camera should look at
 * @param unitsData
 */
export function getCenterAndCamPosition(
  refUnits: ThreeDUnit[] = [],
  elevation: number
): { centerPosition: MapPoints; camPosition: MapPoints; size: number; relativeAlt: number } {
  let minLat = Infinity;
  let maxLat = -Infinity;

  let minLon = Infinity;
  let maxLon = -Infinity;

  let minAlt = Infinity;
  let maxAlt = -Infinity;

  let minAvgAlt = Infinity;

  refUnits.forEach(unitData => {
    const unitCoords = unitData[1] || [];
    let altitudesSum = 0;
    let nrOfAltitudes = 0;

    unitCoords.forEach((triangle: UnitTriangle) => {
      if (!triangle || !triangle.length) return;

      triangle.forEach(([lat, lon, alt]) => {
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;

        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;

        if (alt < minAlt) minAlt = alt;
        if (alt > maxAlt) maxAlt = alt;

        altitudesSum += alt;
        nrOfAltitudes += 1;
      });
    });
    const avgAlt = altitudesSum / nrOfAltitudes;
    if (avgAlt < minAvgAlt) minAvgAlt = avgAlt;
  });

  const height = maxLon - minLon;
  const width = maxLat - minLat;

  const refLong = (minLon + maxLon) / 2;
  const refLat = (minLat + maxLat) / 2;
  const refAlt = minAlt;

  const relativeAlt = minAvgAlt - elevation;

  return {
    centerPosition: [refLat, refLong, refAlt] as MapPoints,
    camPosition: [refLat, refLong, relativeAlt] as LatLngAltTuple,
    size: Math.sqrt(height * height + width * width),
    relativeAlt,
  };
}

function getReferenceUnits(unitsData, context3dUnits) {
  return displaySingleUnit(context3dUnits)
    ? [unitsData.find(([unitClientId], _coords) => unitClientId === context3dUnits[0])]
    : unitsData;
}

/**
 *  From an array of unit triangle coords and a reference position, return the relative coords for the units in the map
 **/
export function getUnitPointsFromRefPos(unitTriangleCoords, projectedRefPosition): UnitPoints {
  const unitPoints = [];

  for (const triangle of unitTriangleCoords) {
    for (const vertex of triangle) {
      // Project current vertex
      // @ts-ignore
      const anchor = new GeoCoordinates(...vertex);
      const position = new THREE.Vector3();
      mercatorProjection.projectPoint(anchor, position);

      // Get its position relative to the ref one
      position.sub(projectedRefPosition);
      unitPoints.push(position.x, position.y, position.z * Z_FACTOR);
    }
  }

  return unitPoints;
}

export function getProjectedReferencePosition([refLat, refLong, refAlt]: [number, number, number]) {
  const refAnchor = new GeoCoordinates(refLat, refLong, refAlt);
  const projectedRefPosition = new THREE.Vector3();
  // Figure out how to use this function without passing whole map...using jsonfn?
  mercatorProjection.projectPoint(refAnchor, projectedRefPosition);
  return projectedRefPosition;
}

/**
 * Adds units to the map and returns the position where the camera should look
 * @param map
 * @param unitToMeshes
 * @param unitsData
 */
export function calculateRelativeCoordsAndPositions(unitsData, context3dUnits = [], elevation) {
  const refUnits = getReferenceUnits(unitsData, context3dUnits);

  const { centerPosition, camPosition, relativeAlt, size } = getCenterAndCamPosition(refUnits, elevation);

  // Project reference lat long position into the map
  const projectedRefPosition = getProjectedReferencePosition(centerPosition);

  // Closer for the small buildings, far for the larger
  const camExtraDistance = size;

  refUnits.forEach(unitData => {
    const [unitClientId, unitCoords] = unitData;
    const unitPoints = getUnitPointsFromRefPos(unitCoords, projectedRefPosition);
    const coords = new Float32Array(unitPoints);
    postMessage({ unitProjected: { unitClientId: unitClientId, coords } }, undefined, [coords.buffer]);
  });

  postMessage({ positions: { centerPosition, camExtraDistance, camPosition }, relativeAlt }, undefined);
}

onmessage = function (e) {
  const { unitsData, context3dUnits, elevation }: StartCalculationMessage = e.data;
  calculateRelativeCoordsAndPositions(unitsData, context3dUnits, elevation);
};
