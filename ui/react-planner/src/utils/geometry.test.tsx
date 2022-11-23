import { cloneDeep, GeometryUtils } from '../utils/export';
import { EPSILON, REFERENCE_LINE_POSITION, SeparatorsType, VERTEX_ROUNDING_PRECISION } from '../constants';
import { addLineToState, getMockState, SELECTED_LAYER_ID } from '../tests/utils/tests-utils';

describe('getHolePositionAfterChangingLine function', () => {
  const MOCK_INITIAL_OFFSET = 0.33;
  it.each([
    ['O degrees', { x: 736, y: 935 }, { x: 899, y: 935 }, MOCK_INITIAL_OFFSET, { x: 789.79, y: 935 }],
    ['30 degrees', { x: 736, y: 935 }, { x: 899, y: 1029.11 }, MOCK_INITIAL_OFFSET, { x: 789.79, y: 966.0563 }],
    ['45 degrees', { x: 736, y: 935 }, { x: 899, y: 1098 }, MOCK_INITIAL_OFFSET, { x: 789.79, y: 988.79 }],
    ['90 degrees', { x: 794, y: 935 }, { x: 794, y: 1400 }, MOCK_INITIAL_OFFSET, { x: 794, y: 1088.45 }],
    // -90 degrees still flips the offset, as we have this angle only when the wall is rotated
  ])(
    'Calculates new hole offset position after rotating the line %s',
    (description, vertex1, vertex2, previousOffset, expectedOffset) => {
      const offsetPosition = GeometryUtils.getHolePositionAfterChangingLine(vertex1, vertex2, previousOffset);
      expect(offsetPosition).toStrictEqual(expectedOffset);
    }
  );
});

describe('PointOnLineGivenAngleAndPoint function', () => {
  it.each([
    [
      'Item is aligned with the X axis (angle is 0 degrees), so the new point is still over the x-axis just shifted along the line',
      { x: 0, y: 0, angle: 0, offset: 30 },
      { x: 30, y: 0 },
    ],
    [
      'Item is aligned with the X axis (angle is 180 degrees), so the new point is still over the x-axis just negatively shifted along the line',
      { x: 0, y: 0, angle: 180, offset: 30 },
      { x: -30, y: 0 },
    ],
    [
      'Item is aligned with the Y axis (angle is 90 degrees), so the new point is still over the y-axis just shifted along the line',
      { x: 0, y: 0, angle: 90, offset: 30 },
      { x: 0, y: 30 },
    ],
    [
      'Item is aligned with the Y axis (angle is 270 degrees), so the new point is still over the y-axis just negatively shifted along the line',
      { x: 0, y: 0, angle: 270, offset: 30 },
      { x: 0, y: -30 },
    ],
    [
      'Item has 45 degrees, so it returns correctly a point over the ramp increasing the same size in x and y',
      { x: 0, y: 0, angle: 45, offset: 30 },
      { x: 21.2132, y: 21.2132 }, // sqrt(2) * 15
    ],
  ])('Calculates the polygon of an opening correctly', (description, properties, expectedPoint) => {
    const { x, y, angle, offset } = properties;
    const point = GeometryUtils.PointOnLineGivenAngleAndPoint(x, y, angle, offset);
    const { x: expectedX, y: expectedY } = expectedPoint;
    const { x: pointX, y: pointY } = point;

    expect(pointX).toBeCloseTo(expectedX, 2);
    expect(pointY).toBeCloseTo(expectedY, 2);
  });
});

describe('getAllAreasLinesFromArea function', () => {
  it.each([
    [
      'should return all the lines as the distance is bigger',
      [
        [
          [
            [0, 0],
            [10, 10],
            [0, 10],
            [0, 0],
          ],
        ],
      ],
      [
        [
          [0, 0],
          [10, 10],
        ],
        [
          [10, 10],
          [0, 10],
        ],
        [
          [0, 10],
          [0, 0],
        ],
      ],
    ],
  ])('%s', (description, areaCoords, expectedCoords) => {
    const allLines = GeometryUtils.getAllAreasLinesFromArea(areaCoords);
    expect(allLines).toStrictEqual(expectedCoords);
  });
});

describe('roundCoord function', () => {
  const TEST_CASES = [
    [1123.1234567891012, 1123.123456789101],
    [112.1234567891012, 112.123456789101],
    [111.123456, 111.123456],
  ];

  it.each(TEST_CASES)(
    `Should round coordinate to the ${VERTEX_ROUNDING_PRECISION}th decimal`,
    (inputCoord, expectedCoord) => {
      const roundedCoord = GeometryUtils.roundCoord(inputCoord);
      expect(roundedCoord).toBe(expectedCoord);
    }
  );
});

describe('getAreaLinesBufferedIfItemInside function', () => {
  it.each([
    [
      'return null if item is not inside of the area',
      [
        [
          [0, 0],
          [10, 10],
          [0, 10],
          [0, 0],
        ],
      ],
      20,
      20,
      null,
    ],
    [
      'return buffered lines of area with interiors if item is inside of the area',
      [
        [
          [0, 0],
          [20, 20],
          [0, 20],
          [0, 0],
        ],
        [
          [7.5, 7.5],
          [12.5, 12.5],
          [7.5, 12.5],
          [7.5, 7.5],
        ],
      ],
      5,
      5,
      [
        [
          [
            [-1.001118849497939, -7.081154551613622e-10],
            [-0.9818826315222281, -0.1953085995880175],
            [-0.9249132146635035, -0.3831115972486184],
            [-0.8323999016627539, -0.5561918322307347],
            [-0.7078979272566174, -0.7078979280962663],
            [-0.5561918324998629, -0.8323999021594342],
            [-0.38311159753626195, -0.9249132149814576],
            [-0.19530859873094145, -0.9818826314806901],
            [-6.693687812385008e-12, -1.0011188499807335],
            [0.1953085987177526, -0.9818826314806901],
            [0.3831115975239091, -0.9249132149814576],
            [0.55619183248875, -0.8323999021594342],
            [0.7078979272471563, -0.7078979280962663],
            [20.707897927247025, 19.292102070897652],
            [20.832399901657414, 19.443808167617576],
            [20.92491321466207, 19.61688840228557],
            [20.9818826315243, 19.804691400201243],
            [21.001118849502856, 19.999999999168566],
            [20.98188263152862, 20.19530859782014],
            [20.92491321467056, 20.38311159569906],
            [20.832399901669696, 20.556191831785963],
            [20.707897927262625, 20.70789792676362],
            [20.556191832504354, 20.832399900269486],
            [20.383111597538647, 20.924913213326015],
            [20.1953085987309, 20.98188262959366],
            [20.00000000000416, 21.001118848356555],
            [-4.158568356403035e-12, 21.001118848356555],
            [-0.19530859872976236, 20.98188262959366],
            [-0.3831115975365442, 20.924913213326015],
            [-0.5561918325015053, 20.832399900269486],
            [-0.7078979272594402, 20.70789792676362],
            [-0.8323999016665599, 20.556191831785963],
            [-0.924913214667943, 20.38311159569906],
            [-0.981882631527081, 20.195308599236366],
            [-1.0011188495028556, 19.999999999168566],
            [-1.001118849497939, -7.081154551613622e-10],
          ],
          [
            [8.501118849499724, 9.916914702223421],
            [8.501118849500081, 11.498881150372243],
            [10.083085295952968, 11.498881150372243],
            [8.501118849499724, 9.916914702223421],
          ],
        ],
        [
          [
            [8.501118849499724, 9.916914702223421],
            [10.083085295952968, 11.498881150372243],
            [8.501118849500081, 11.498881150372243],
            [8.501118849499724, 9.916914702223421],
          ],
        ],
      ],
    ],
    [
      'return lines buffered if item is inside of the area',
      [
        [
          [0, 0],
          [10, 10],
          [0, 10],
          [0, 0],
        ],
      ],
      5,
      5,
      [
        [
          [
            [-1.0011188494982586, -7.081154551613622e-10],
            [-0.9818826315223262, -0.1953085995880175],
            [-0.9249132146634745, -0.3831115972486184],
            [-0.8323999016627417, -0.5561918322307347],
            [-0.7078979272565992, -0.7078979280962663],
            [-0.5561918324999751, -0.8323999021594342],
            [-0.3831115975365388, -0.9249132149814576],
            [-0.1953085987313547, -0.9818826314806901],
            [-7.33658438193611e-12, -1.0011188499807335],
            [0.19530859871701856, -0.9818826314806901],
            [0.383111597523042, -0.9249132149814576],
            [0.5561918324878201, -0.8323999021594342],
            [0.7078979272462859, -0.7078979280962663],
            [10.70789792724622, 9.292102071499682],
            [10.83239990165589, 9.443808166730426],
            [10.924913214659856, 9.616888402263807],
            [10.981882631521461, 9.804691400052175],
            [11.001118849499486, 9.999999999330084],
            [10.981882631524787, 10.195308596876025],
            [10.924913214666367, 10.383111596043893],
            [10.832399901665301, 10.556191831579996],
            [10.707897927258177, 10.70789792648475],
            [10.556191832499975, 10.83239990116862],
            [10.383111597534588, 10.924913213401275],
            [10.195308598727216, 10.981882629766435],
            [10.000000000001055, 11.001118848948176],
            [-1.0548365983601072e-12, 11.001118848948176],
            [-0.19530859872624667, 10.981882629766435],
            [-0.3831115975327699, 10.924913213401275],
            [-0.5561918324975283, 10.83239990116862],
            [-0.7078979272553896, 10.70789792648475],
            [-0.8323999016625695, 10.556191831579996],
            [-0.924913214664087, 10.383111596043893],
            [-0.9818826315234223, 10.195308598292252],
            [-1.0011188494994876, 9.999999999330084],
            [-1.0011188494982586, -7.081154551613622e-10],
          ],
        ],
      ],
    ],
  ])('%s', (description, areaCoords, itemX, itemY, expectedCoords) => {
    const bufferValue = 1.0;
    const linesBuffered = GeometryUtils.getAreaLinesBufferedIfItemInside(areaCoords, bufferValue, itemX, itemY);
    expect(linesBuffered).toStrictEqual(expectedCoords);
  });
});

describe('getItemPolygon function', () => {
  it.each([
    [
      'A square item without angle is correctly generated',
      [10, 10, 0, 4, 4],
      [
        [
          [8, 7.999999998969416],
          [12, 7.999999998969416],
          [12, 11.999999999937685],
          [8, 11.999999999937685],
          [8, 7.999999998969416],
        ],
      ],
    ],
    [
      'A square item with 90 degrees angle is still almost the same',
      [10, 10, 90, 4, 4],
      [
        [
          [11.99999999637567, 7.999999998969416],
          [11.99999999637567, 11.999999999937685],
          [7.999999997583781, 11.999999998521456],
          [7.999999997583781, 8.000000000385644],
          [11.99999999637567, 7.999999998969416],
        ],
      ],
    ],
    [
      'A square item with 45 degrees angle has also the right position (matching the BE calculation)',
      [10, 10, 45, 4, 4],
      [
        [
          [9.999999996979726, 7.171572875274159],
          [12.828427127076399, 9.999999999330084],
          [9.999999996979726, 12.828427123879877],
          [7.171572879538613, 9.999999999330084],
          [9.999999996979726, 7.171572875274159],
        ],
      ],
    ],
    [
      'A rectangle item without angle is correctly generated',
      [10, 10, 0, 2, 5],
      [
        [
          [9.000000000000002, 7.499999998962111],
          [11, 7.499999998962111],
          [11, 12.499999999818344],
          [9.000000000000002, 12.499999999818344],
          [9.000000000000002, 7.499999998962111],
        ],
      ],
    ],
  ])('%s', (description, itemValues, expectedCoords) => {
    const [x, y, angle, itemWidth, itemLength] = itemValues;
    const itemPolygon = GeometryUtils.getItemPolygon(x, y, angle, itemWidth, itemLength);
    const newCoordinates = itemPolygon['geometry']['coordinates'];
    expect(newCoordinates).toStrictEqual(expectedCoords);
  });
});

describe('isPointOnLine', () => {
  const TEST_CASES = [
    [{ x: 0, y: 0 }, { x1: 0, y1: 0, x2: 10, y2: 10 }, true],
    [{ x: 5, y: 5 }, { x1: 0, y1: 0, x2: 10, y2: 10 }, true],
    [{ x: 5.9, y: 5.9 }, { x1: 0, y1: 0, x2: 10, y2: 10 }, true], // here we are in theory within 1 pixel tolerance
    [{ x: 6, y: 5 }, { x1: 0, y1: 0, x2: 10, y2: 10 }, false],
  ];
  it.each(TEST_CASES)(
    `detect correctly different cases to check if the tolerance is correctly set`,
    (point, line, expected) => {
      expect(GeometryUtils.isPointOnLine(point, line)).toBe(expected);
    }
  );
});

describe('cooordinate geometry utils', () => {
  it.each([
    [
      [
        [1, 1],
        [2, 1],
      ],
      [
        [1, 1],
        [2, 1],
      ],
      [
        [2, 1],
        [2, 1.001],
      ],
      [
        [2, 1],
        [2, 1.001],
      ],
      [
        [5, 1],
        [1, 5],
      ],
      [
        [1, 5],
        [5, 1],
      ],
      [
        [1, 2],
        [1, 1],
      ],
      [
        [1, 1],
        [1, 2],
      ],
    ],
  ])('orders coordinates ascendingly', (coords, expectedCoords) => {
    expect(GeometryUtils.orderCoords(coords)).toStrictEqual(expectedCoords);
  });

  it.each([
    [[0, 0], [0, 0], true],
    [[1.000002, 0], [1, 0], false],
    [[1.00000001, 0], [1, 0], true],
    [[0, 0], [1e-5, 0], false],
    [[EPSILON, EPSILON], [EPSILON, EPSILON], true],
  ])('returns true of false if coordinate pairs have the same values', (c1, c2, shouldBeSame) => {
    expect(GeometryUtils.sameCoords(c1, c2)).toBe(shouldBeSame);
  });

  it.each([
    [
      [
        [0, 0],
        [0, 3],
        [3, 1],
        [0, 1],
        [0, 0],
      ],
      [
        [0, 0],
        [0, 3],
        [3, 1],
        [0, 1],
      ],
    ],
    [
      [
        [0, 0],
        [0, 5],
        [0, 5],
        [0, 5],
        [1, 5],
        [1, 0],
      ],
      [
        [0, 0],
        [0, 5],
        [1, 5],
        [1, 0],
      ],
    ],
    [
      [
        [0, 0],
        [0, 5],
        [1, 5],
        [1, 0],
      ],
      [
        [0, 0],
        [0, 5],
        [1, 5],
        [1, 0],
      ],
    ],
  ])('removes duplicate points from the coordinate GeoJSON array', (coords, expectedCoords) => {
    expect(GeometryUtils.getUniquePolygonPoints([coords])).toStrictEqual(expectedCoords);
  });

  it.each([
    [
      [
        [0, 0],
        [0, 2],
        [2, 2],
        [2, 0],
        [0, 0],
      ],
      [1, 1],
      [
        [0, 0],
        [5, 0],
        [5, 1],
        [0, 1],
        [0, 0],
      ],
      [2.5, 0.5],
    ],
  ])('returns feature centroid', (featureCoordinates, expectedCentroid) => {
    expect(GeometryUtils.getFeatureCentroid(featureCoordinates)).toStrictEqual(expectedCentroid);
  });

  it('raises error if an empty coordinate array was passed to getFeatureCentroid', () => {
    expect(() => GeometryUtils.getFeatureCentroid([])).toThrowError(
      'Passed empty feature coordinate error to get centroid.'
    );
  });
});

describe('getPostProcessableIntersectingLines', () => {
  let state;

  const MOCK_LINE_PROPERTIES = {
    width: { value: 20 },
    referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
  };
  beforeEach(() => {
    state = getMockState();
  });

  const l1 = { x0: 1598, y0: 300, x1: 1598, y1: 400 };
  const l2 = { x0: l1.x1, y0: l1.y1, x1: 1699, y1: 400 };

  const t1 = { x0: 1399, y0: 400, x1: 1501, y1: 400 };
  const t2 = { x0: 1447, y0: 337, x1: 1447, y1: 392 };

  it.each([
    ['L case: Two perpendicular lines', 1, l1, l2],
    ['T case: One line crossing another', 1, t1, t2],
    ['No lines intersecting', 0, l1, t2],
  ])('With %s finds: %d line(s)', (description, expectedPostProcessedLines, line1Points, line2Points) => {
    const line1Result = addLineToState(state, SeparatorsType.WALL, { ...line1Points }, MOCK_LINE_PROPERTIES);
    state = line1Result.updatedState;
    const originalLine = line1Result.line;

    const line2Result = addLineToState(state, SeparatorsType.WALL, { ...line2Points }, MOCK_LINE_PROPERTIES);
    state = line2Result.updatedState;
    const line = line2Result.line;

    const layer = state.scene.layers[SELECTED_LAYER_ID];
    const linesToPostProcess = GeometryUtils.getPostProcessableIntersectingLines(layer, line.id);
    expect(linesToPostProcess).toHaveLength(expectedPostProcessedLines);

    // Postprocess line is always the one we connect to
    if (expectedPostProcessedLines) {
      const [postprocessableLine] = linesToPostProcess;
      expect(postprocessableLine.id).toBe(originalLine.id);
    }
  });
});

describe('getTwoClosestVerticesToLine', () => {
  it.each([
    [
      // horizontal
      { x1: 0, y1: 0, x2: 1, y2: 0 },
      [
        { x: 1.001, y: 0 },
        { x: 0.75, y: 0.05 },
        { x: 0.5, y: -0.1 },
        { x: 0, y: 0 },
      ],
      [
        { x: 0, y: 0 },
        { x: 1.001, y: 0 },
      ],
    ],
    [
      // diagonal
      { x1: 0, y1: 0, x2: 10, y2: 10 },
      [
        { x: 2.5, y: 2.75 },
        { x: 5, y: 5.001 },
        { x: 7.5, y: 7.57 },
        { x: 9.99, y: 10 },
      ],
      [
        { x: 5, y: 5.001 },
        { x: 9.99, y: 10 },
      ],
    ],
    [
      // vertical
      { x1: 0, y1: 0, x2: 0, y2: 10 },
      [
        { x: 2.5, y: 0.1 },
        { x: 1.2, y: 5.001 },
        { x: -1.5, y: 5.001 },
        { x: 2.0, y: 10 },
      ],
      [
        { x: 1.2, y: 5.001 },
        { x: -1.5, y: 5.001 },
      ],
    ],
  ])('should return two closest points to the reference line', (line, inputVertices, expectedVertices) => {
    expect(GeometryUtils.getTwoClosestVerticesToLine(inputVertices, line)).toStrictEqual(expectedVertices);
  });
});

describe('getSimplifiedPolygon', () => {
  it.each([
    [
      [
        // rectangle
        [100, 0],
        [0, 0],
        [0, 10],
        [100, 10],
        [100, 0],
      ],
    ],
    [
      [
        // trapezoid
        [15, 0],
        [0, 0],
        [0, 1],
        [10, 1],
        [15, 0],
      ],
    ],
    [
      // rhombus
      [
        [15, 0],
        [0, 0],
        [5, 1],
        [20, 1],
        [15, 0],
      ],
    ],
  ])('should return the same valid polygon', inputCoords => {
    const polygon = GeometryUtils.createPolygon([inputCoords]);
    const simplifiedPolygon = GeometryUtils.getSimplifiedPolygon(polygon);
    expect(polygon.geometry.coordinates).toStrictEqual(simplifiedPolygon.geometry.coordinates);
  });

  it.each([
    [
      [
        [100, 0],
        [0, 0],
        [0, 10],
        [50, 10 + 1e-5],
        [100, 10],
        [100, 0],
      ],
      3,
    ],
    [
      [
        [0, 0],
        [-1e-7, 5],
        [0, 10],
        [100, 10],
        [100, 0],
        [0, 0],
      ],
      1,
    ],
    [
      [
        [100, 0],
        [0, 0],
        [0, 10],
        [100, 10],
        [100.001, 5],
        [100, 0],
      ],
      4,
    ],
  ])('should return a polygon with 1 coord pair less if within tolerance', (inputCoords, redundantCoordIndex) => {
    const coordinates = cloneDeep(inputCoords);
    const polygon = GeometryUtils.createPolygon([coordinates]);
    const simplifiedPolygon = GeometryUtils.getSimplifiedPolygon(polygon);
    // remove the odd one out
    coordinates.splice(redundantCoordIndex, 1);
    expect([coordinates]).toStrictEqual(simplifiedPolygon.geometry.coordinates);
  });

  it('should return same polygon if invalid coordinates outside of simplification tolerance', () => {
    const polygonCoords = [
      [100, 0],
      [0, 0],
      [0, 10],
      [50, 11],
      [100, 10],
      [100, 0],
    ];
    const polygon = GeometryUtils.createPolygon([polygonCoords]);
    const simplifiedPolygon = GeometryUtils.getSimplifiedPolygon(polygon);
    expect(polygon.geometry.coordinates).toStrictEqual(simplifiedPolygon.geometry.coordinates);
  });
});

describe('getPolygonCenterLine', () => {
  it.each([
    [
      [
        [0, 0],
        [0, 2],
        [10, 2],
        [10, 0],
        [0, 0],
      ],
      [
        [0, 1],
        [10, 1],
      ],
    ],
    [
      [
        [1, 5],
        [1, 10],
        [2, 10],
        [2, 5],
        [1, 5],
      ],
      [
        [1.5, 10],
        [1.5, 5],
      ],
    ],
    [
      [
        [-5, -5],
        [-6, -4],
        [-1, 1],
        [0, 0],
        [-5, -5],
      ],
      [
        [-5.5, -4.5],
        [-0.5, 0.5],
      ],
    ],
  ])('should get the longest center line of rectangle polygon', (polygonCoords, expectedLineCoords) => {
    const polygon = GeometryUtils.createPolygon([polygonCoords]);
    const expectedLineString = GeometryUtils.getLineString(expectedLineCoords);
    expect(GeometryUtils.getPolygonCenterLine(polygon)).toStrictEqual(expectedLineString);
  });
});
