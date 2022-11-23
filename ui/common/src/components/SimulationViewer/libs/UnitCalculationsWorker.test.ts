import * as THREE from 'three';
import { UnitPoints, UnitTriangle } from '../../../types';
import { getCenterAndCamPosition, getUnitPointsFromRefPos } from './UnitCalculationsWorker';
import { mockedUnitsTriangles1, mockedUnitsTriangles2, mockedUnitsTriangles3 } from './__fixtures__/unitTriangles';

// Mock taken from calibrator 401
const MOCK_PROJECTED_REF_POSITION = { x: 20989870.555931255, y: 26047540.86080679, z: 428.651395361328 };
const MOCK_PROJECTED_POSITION = new THREE.Vector3(20989845.681845035, 26047539.508774165, 428.651395361328);

jest.mock('@here/harp-geoutils', () => {
  return {
    ...jest.requireActual('@here/harp-geoutils'),
    mercatorProjection: {
      projectPoint: (anchor, pos) => {
        return pos.set(MOCK_PROJECTED_POSITION.x, MOCK_PROJECTED_POSITION.y, MOCK_PROJECTED_POSITION.y);
      },
    },
  };
});

describe('getCenterAndCamPosition', () => {
  it.each([
    [mockedUnitsTriangles1, { camPosition: [3, 4, 250], centerPosition: [3, 4, 249], size: 5.656854249492381 }],
    [mockedUnitsTriangles2, { camPosition: [4.5, 5.5, 250], centerPosition: [4.5, 5.5, 249], size: 9.899494936611665 }],
    [mockedUnitsTriangles3, { camPosition: [4.5, 4, 240], centerPosition: [4.5, 4, 239], size: 12.206555615733702 }],
  ])('Get ref coordinate and cam coordinate from a set of reference units: %#', (refUnits, expectedOutput) => {
    const { relativeAlt, ...rest } = getCenterAndCamPosition(refUnits, 0);
    expect(rest).toStrictEqual(expectedOutput);
  });

  it.each([
    [mockedUnitsTriangles1, 245, 5],
    [mockedUnitsTriangles2, 245, 5],
    [mockedUnitsTriangles3, 230, 10],
  ])('finds relative altitude of given triangles:  %#', (refUnits, elevation, expectedOutput) => {
    const { relativeAlt } = getCenterAndCamPosition(refUnits, elevation);
    expect(relativeAlt).toBe(expectedOutput);
  });
});

it('should get unit local points from an array of lat lon coordinates and a reference position', () => {
  const MOCK_UNIT_COORDS: UnitTriangle[] = [
    [
      [47.414731864983274, 8.555426070088082, 428.651395361328],
      [47.414731865541604, 8.55542607054877, 431.251595361328],
      [47.414732084480804, 8.555397659402207, 431.251595361328],
    ],
    [
      [47.414731864983274, 8.555426070088082, 428.651395361328],
      [47.414732084480804, 8.555397659402207, 431.251595361328],
      [47.41473208392247, 8.555397658941523, 428.651395361328],
    ],
    [
      [47.41473208392247, 8.555397658941523, 428.651395361328],
      [47.414732084480804, 8.555397659402207, 431.251595361328],
      [47.41473409897564, 8.555397693095417, 431.251595361328],
    ],
  ];

  const EXPECTED_OUTPUT = [
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
    -24.8740862198174,
    -1.3520326241850853,
    39852079.61178957,
  ];

  const unitPoints: UnitPoints = getUnitPointsFromRefPos(MOCK_UNIT_COORDS, MOCK_PROJECTED_REF_POSITION);

  expect(unitPoints).toEqual(EXPECTED_OUTPUT);
});
