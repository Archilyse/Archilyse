import { calculateDomain, calculateRelative, computeHexagonColors, getRotatedPoint } from './SimRenderer';

const MOCKED_OBSERVATION_POINTS = [
  // LV95 coords
  [1214526.970112225, 2663634.1306005726, 467.957897949219],
  [1214526.7201844628, 2663634.1245911093, 467.957897949219],
  [1214526.4702567006, 2663634.1185816457, 467.957897949219],
  [1214526.2203289384, 2663634.1125721824, 467.957897949219],
  [1214525.970401176, 2663634.1065627187, 467.957897949219],
];
const MOCKED_HEXAGON_VALUES = [
  0.0077080270275473595,
  0.016030702739953995,
  0.03817766532301903,
  0.10201816260814667,
  0.20488502085208893,
];

it('should calculate a relative point', () => {
  const coordinate = {
    x: 2,
    y: 2,
    z: 2,
  };

  const referenceCoordinate = {
    x: 1,
    y: 2,
    z: 3,
  };

  const result = calculateRelative(coordinate, referenceCoordinate);
  expect(result[0]).toBe(1);
  expect(result[1]).toBe(0);
  expect(result[2]).toBe(-1);
});

it('calculate domain correctly', () => {
  const domainFunction = calculateDomain(0, 100);

  // Blue for the 0 value
  expect(domainFunction(0)).toBe('rgb(44, 123, 182)');

  // Yellow for the 50 value
  expect(domainFunction(50)).toBe('rgb(255, 255, 140)');

  // Red for the 100 value
  expect(domainFunction(100)).toBe('rgb(215, 25, 28)');
});

it('computes hexagon colors', () => {
  const EXPECTED_RGB_COLOR_ARRAY = [
    0.1725490242242813,
    0.48235294222831726,
    0.7137255072593689,
    0.1725490242242813,
    0.48235294222831726,
    0.7137255072593689,
    0.1725490242242813,
    0.48235294222831726,
    0.7137255072593689,
    0.1725490242242813,
    0.48235294222831726,
    0.7137255072593689,
    0.16862745583057404,
    0.48627451062202454,
    0.7137255072593689,
  ];
  const domainFunction = calculateDomain(0, 100);
  const colors = computeHexagonColors(MOCKED_OBSERVATION_POINTS, MOCKED_HEXAGON_VALUES, domainFunction);
  expect(colors instanceof Float32Array).toBe(true);
  expect(Array.from(colors)).toEqual(EXPECTED_RGB_COLOR_ARRAY);
});

it('should rotate a point x degrees', () => {
  const originalY = 50;
  const originalX = 50;
  const rotatedPoint0deg = getRotatedPoint(originalX, originalY, 0);
  expect(rotatedPoint0deg.x).toBe(originalX);
  expect(rotatedPoint0deg.y).toBe(originalY);

  const rotatedPoint10deg = getRotatedPoint(originalX, originalY, 10);
  expect(rotatedPoint10deg.x).toBeCloseTo(57.9, 0);
  expect(rotatedPoint10deg.y).toBeCloseTo(40.5, 0);

  const rotatedPoint45deg = getRotatedPoint(originalX, originalY, 45);
  expect(rotatedPoint45deg.x).toBeCloseTo(70.7, 0);
  expect(rotatedPoint45deg.y).toBeCloseTo(0.0, 0);

  // Distance to origin didn't change.
  const segmentLength = Math.sqrt(Math.pow(originalX, 2) + Math.pow(originalY, 2));
  expect(rotatedPoint45deg.x).toBeCloseTo(segmentLength, 0);
});
