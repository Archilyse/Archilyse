import { bboxPolygon, transformRotate, transformTranslate } from '@turf/turf';
import {
  ACCEPTED_NUMBER_OF_COORDINATES,
  ACCEPTED_NUMBER_OF_POLYGON_EDGES,
  REFERENCE_LINE_POSITION,
  SeparatorsType,
} from '../constants';
import { addLineToState, getCleanMockState, getMockState, SELECTED_LAYER_ID } from '../tests/utils/tests-utils';
import { GeometryUtils, PostProcessor } from '../utils/export';
import { MOCK_SCENE_WITH_POTENTIAL_ORPHAN_OPENINGS, MOCK_STATE } from '../tests/utils';

const defaultLineProperties = {
  height: {
    unit: 'cm',
    value: 300,
  },
  referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
  width: {
    unit: 'cm',
    value: 20,
  },
};

/*
 *  (0, 0)             (100, 0)
 *     ×────────────────×
 *     │               /
 *     │              /
 *     │             × (85, -15)
 *     │             \
 *     ×──────────────×
 * (0, -20)         (90, -20)
 */
const postProcessedLineCoords = [
  [0, -20],
  [90, -20],
  [85, -15],
  [100, 0],
  [0, 0],
  [0, -20],
];

const getLine = (
  linePoints: { x0: number; y0: number; x1: number; y1: number },
  lineProperties: any = defaultLineProperties
) => {
  return addLineToState(getCleanMockState(), SeparatorsType.WALL, linePoints, lineProperties);
};

const addDummyLineWithCoordinates = (state, coordinates) => {
  const firstLinePoints = { x0: 0, y0: 10, x1: 0, y1: 10 };
  const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, firstLinePoints, defaultLineProperties);
  state = {
    ...updatedState,
    scene: {
      ...updatedState.scene,
      layers: {
        ...updatedState.scene.layers,
        [SELECTED_LAYER_ID]: {
          ...updatedState.scene.layers[SELECTED_LAYER_ID],
          lines: {
            ...updatedState.scene.layers[SELECTED_LAYER_ID].lines,
            [line.id]: {
              ...updatedState.scene.layers[SELECTED_LAYER_ID].lines[line.id],
              coordinates: [coordinates],
            },
          },
        },
      },
    },
  };
  const updatedLine = state.scene.layers[SELECTED_LAYER_ID].lines[line.id];
  return { updatedState: state, line: updatedLine };
};

describe('isValid', () => {
  let state;
  let lineID;

  beforeEach(() => {
    state = getMockState();
    const allLines = Object.values(state.scene.layers[SELECTED_LAYER_ID].lines) as any;
    lineID = allLines[0].id;
  });

  it(`Postprocessed line with more than ${ACCEPTED_NUMBER_OF_POLYGON_EDGES} edges is not valid`, () => {
    const coordinatesOfPolygonWithTooManyEdges = [
      [
        [1393.2729047937592, 236.09684222090695],
        [1393.2729047937592, 236.09684222090695],
        [1375.534490265913, 237.70334014041],
        [1403.618321044486, 547.795638320484],
        [1419.8891568443973, 529.9846252800345],
        [1393.2729047937592, 236.09684222090695],
      ],
    ];
    state = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          [SELECTED_LAYER_ID]: {
            ...state.scene.layers[SELECTED_LAYER_ID],
            lines: {
              ...state.scene.layers[SELECTED_LAYER_ID].lines,
              [lineID]: {
                ...state.scene.layers[SELECTED_LAYER_ID].lines[lineID],
                coordinates: coordinatesOfPolygonWithTooManyEdges,
              },
            },
          },
        },
      },
    };

    const isValid = PostProcessor.isValid(state, [lineID]);
    expect(isValid).toBe(false);
  });

  it(`Postprocessed line with an incorrect number of vertices is not valid`, () => {
    // Artificially set an incorrect number of vertices
    state = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          [SELECTED_LAYER_ID]: {
            ...state.scene.layers[SELECTED_LAYER_ID],
            lines: {
              ...state.scene.layers[SELECTED_LAYER_ID].lines,
              [lineID]: {
                ...state.scene.layers[SELECTED_LAYER_ID].lines[lineID],
                coordinates: [
                  [
                    // external linearRing
                    [-121.6021728515625, 47.05141149430736],
                    [-121.33300781249999, 46.83389173208538],
                    [-120.67932128906249, 46.976504510552],
                    [-120.684814453125, 47.4057852900587],
                    [-121.25610351562499, 47.41322033016902],
                    [-121.640625, 47.327653995607115],
                    [-121.6021728515625, 47.05141149430736],
                  ],
                  [
                    // internal linearRing
                    [-121.343994140625, 47.156104775044035],
                    [-121.2615966796875, 47.010225655683485],
                    [-120.91003417968749, 47.148633511301426],
                    [-121.09130859375, 47.27922900257082],
                    [-121.343994140625, 47.156104775044035],
                  ],
                ],
              },
            },
          },
        },
      },
    };

    const isValid = PostProcessor.isValid(state, [lineID]);
    expect(isValid).toBe(false);
  });

  it(`Postprocessed line with correct number of vertices and edges is valid`, () => {
    const coordinatesOfPolygon = [
      // Taken from a correct postprocessed polygon
      [
        [263.7720867050703, 968.9399498437324],
        [105.09556205193758, 968.9399498464827],
        [105.09556205193758, 986.7509628869323],
        [263.772086705379, 986.750962884182],
        [263.7720867050703, 968.9399498437324],
      ],
    ];

    state = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          [SELECTED_LAYER_ID]: {
            ...state.scene.layers[SELECTED_LAYER_ID],
            lines: {
              ...state.scene.layers[SELECTED_LAYER_ID].lines,
              [lineID]: {
                ...state.scene.layers[SELECTED_LAYER_ID].lines[lineID],
                coordinates: coordinatesOfPolygon,
              },
            },
          },
        },
      },
    };
    const isValid = PostProcessor.isValid(state, [lineID]);
    expect(isValid).toBe(true);
  });
  it(`Postprocessed lines with repeated vertices coords are not valid`, () => {
    const line = state.scene.layers[SELECTED_LAYER_ID].lines[lineID];

    // Set two aux vertices with the same coords
    const [aux1, aux2] = line.auxVertices;
    const auxVertex1 = state.scene.layers[SELECTED_LAYER_ID].vertices[aux1];
    const auxVertex2 = state.scene.layers[SELECTED_LAYER_ID].vertices[aux2];
    state.scene.layers[SELECTED_LAYER_ID].vertices[aux1] = { ...auxVertex1, ...{ x: 10.5, y: 5 } };
    state.scene.layers[SELECTED_LAYER_ID].vertices[aux2] = { ...auxVertex2, ...{ x: 10.5, y: 5 } };

    // Line should not be valid
    const isValid = PostProcessor.isValid(state, [lineID]);
    expect(isValid).toBe(false);
  });
});

describe('postprocessLines', () => {
  const createTwoIntersectingLines = state => {
    const { updatedState: stateWithOneLine, line: line1 } = addLineToState(
      state,
      SeparatorsType.WALL,
      { x0: 0, y0: 0, x1: 100, y1: 0 },
      defaultLineProperties
    );
    const { updatedState: stateWithTwoLines, line: line2 } = addLineToState(
      stateWithOneLine,
      SeparatorsType.WALL,
      { x0: 100, y0: 0, x1: 150, y1: -50 },
      defaultLineProperties
    );
    return { updatedState: stateWithTwoLines, mainLineID: line1.id, otherLineID: line2.id };
  };
  let state, mainLineID, otherLineID;
  let postprocessLineSpy, intersectingLinesSpy;

  beforeEach(() => {
    const stateWithLines = createTwoIntersectingLines(getCleanMockState());
    state = stateWithLines.updatedState;
    mainLineID = stateWithLines.mainLineID;
    otherLineID = stateWithLines.otherLineID;
    postprocessLineSpy = jest.spyOn(PostProcessor, 'postprocessLine');
    intersectingLinesSpy = jest.spyOn(GeometryUtils, 'getPostProcessableIntersectingLines');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should post-process each intersecting line until the queue is exhausted', () => {
    const finalState = PostProcessor.postprocessLines(state, 'layer-1', mainLineID).updatedState;
    expect(postprocessLineSpy).toHaveBeenCalledTimes(2);

    const postprocessingCandidates = GeometryUtils.getPostProcessableIntersectingLines(
      finalState.scene.layers['layer-1'],
      mainLineID
    );
    expect(postprocessingCandidates.length).toStrictEqual(0);
  });
  it('should avoid infinite loops', () => {
    // should run exactly n times, where n = total amount of intersecting lines
    intersectingLinesSpy.mockImplementation((layer: any, lineID) => {
      if (lineID == mainLineID) return [layer.lines[otherLineID]];
      else return [layer.lines[mainLineID]];
    });
    const { postprocessedLineIDs } = PostProcessor.postprocessLines(state, 'layer-1', mainLineID);
    expect(postprocessedLineIDs).toStrictEqual([mainLineID, otherLineID]);
    expect(intersectingLinesSpy).toHaveBeenCalledTimes(3);
    expect(postprocessLineSpy).toHaveBeenCalledTimes(2);
  });
  it('should not post-process if there are no intersecting lines', () => {
    const linePoints = { x0: 0, y0: 0, x1: 100, y1: 0 };
    const { updatedState, line } = getLine(linePoints);
    const { postprocessedLineIDs } = PostProcessor.postprocessLines(updatedState, 'layer-1', line.id);
    expect(postprocessedLineIDs).toStrictEqual([line.id]);
    expect(postprocessLineSpy).not.toHaveBeenCalled();
  });

  it('should remove holes if the postprocessed lines leave orphan openings', () => {
    const state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE_WITH_POTENTIAL_ORPHAN_OPENINGS });

    const layerLines = state.scene.layers[SELECTED_LAYER_ID].lines;
    const MOCK_INTERSECT_LINES = [
      // Taken from real case modifying line fe433b2f-bb03-4eef-8dd0-7c0993d3acf5 in `3_rooms_2_w_stairs.json` fixture
      layerLines['26fc202c-8f07-4ac7-91b3-0500b56f9fcf'],
      layerLines['8cef3337-6c8c-44c3-a8c3-0093fdef8405'],
      layerLines['c429b58c-5bbf-4568-b650-c02d468ca8d0'],
    ];

    const holes = state.scene.layers[SELECTED_LAYER_ID].holes;

    // Originally there is one hole associated to a line
    expect(Object.keys(holes).length).toBe(1);
    const lineIDWithAHole = Object.values(holes)[0].line;
    expect(lineIDWithAHole).toBeTruthy();

    const { updatedState, postprocessedLineIDs } = PostProcessor.postprocessLines(
      state,
      SELECTED_LAYER_ID,
      lineIDWithAHole,
      MOCK_INTERSECT_LINES
    );

    // After postprocessing: No holes and postprocessed line removes the relationship

    const holesAfterPostprocess = updatedState.scene.layers[SELECTED_LAYER_ID].holes;

    // No holes
    expect(Object.keys(holesAfterPostprocess).length).toBe(0);

    // Line has been postprocessed and does not include the hole now
    expect(postprocessedLineIDs.includes(lineIDWithAHole)).toBe(true);
    const postprocessedLine = updatedState.scene.layers[SELECTED_LAYER_ID].lines[lineIDWithAHole];
    expect(postprocessedLine.holes.length).toBe(0);
  });
});

describe('extractCoordsAndVerticesFromPolygon', () => {
  it('Should return rounded vertices, auxVertices and distribute them properly', () => {
    const EXPECTED_VERTICES_POINTS = [
      { x: 1511.544722843331, y: 647.696009884998 },
      { x: 1896.099597720947, y: 647.696009883443 },
    ];

    const EXPECTED_AUX_VERTICES_POINTS = [
      { x: 1511.544722843331, y: 638.790503364773 },
      { x: 1891.646844460871, y: 638.790503363236 },
      { x: 1887.194091200796, y: 629.88499684303 },
      { x: 1511.544722843331, y: 629.884996844548 },
    ];
    // Coords and points from a real case that generates 1 main vertex and 5 aux vertex without rounding them
    const linePoints = { x0: 1511.544722843331, y0: 647.696009884998, x1: 1896.099597720947, y1: 647.696009883443 };
    const rawLineCoordinates = [
      [1511.5447228433306, 629.8849968445485],
      [1887.1940912007958, 629.8849968430295],
      [1896.099597720947, 647.696009883443],
      [1511.5447228433306, 647.696009884998],
      [1511.5447228433306, 629.8849968445485],
    ];
    const lineProperties = { ...defaultLineProperties, width: { unit: 'cm', value: 17.811 } };
    const { updatedState: state, line: line } = getLine(linePoints, lineProperties);

    const linePolygon = GeometryUtils.createPolygon([rawLineCoordinates]);
    const { vertices, auxVertices } = PostProcessor.extractCoordsAndVerticesFromPolygon(state, line.id, linePolygon);

    // All vertices are rounded
    [...vertices, ...auxVertices].forEach(vertex => {
      expect(vertex.x).toEqual(GeometryUtils.roundCoord(vertex.x));
      expect(vertex.y).toEqual(GeometryUtils.roundCoord(vertex.y));
    });

    // And distributed properly
    expect(vertices.length).toBe(2);
    expect(auxVertices.length).toBe(4);

    expect(vertices).toStrictEqual(EXPECTED_VERTICES_POINTS);
    expect(auxVertices).toStrictEqual(EXPECTED_AUX_VERTICES_POINTS);
  });

  it.each([
    [
      postProcessedLineCoords,
      [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
      ],
      [
        { x: 0, y: -10 },
        { x: 95, y: -10 },
        { x: 0, y: -20 },
        { x: 90, y: -20 },
      ],
      [
        [90, -20],
        [0, -20],
        [0, 0],
        [100, 0],
        [90, -20],
      ],
    ],
  ])(
    'should return vertices, auxVertices and coordinates for intersections at obtuse angle',
    (lineCoordinates, expectedVertices, expectedAuxVertices, expectedCoordinates) => {
      const linePoints = { x0: 0, y0: 0, x1: 100, y1: 0 };
      const { updatedState: state, line: line } = getLine(linePoints);

      const linePolygon = GeometryUtils.createPolygon([lineCoordinates]);
      const { vertices, auxVertices, coordinates } = PostProcessor.extractCoordsAndVerticesFromPolygon(
        state,
        line.id,
        linePolygon
      );
      expect(vertices.length).toBe(2);
      expect(auxVertices.length).toBe(4);
      expect(coordinates[0].length).toBe(5);

      expect(vertices).toStrictEqual(expectedVertices);
      expect(auxVertices).toStrictEqual(expectedAuxVertices);
      expect(coordinates[0]).toStrictEqual(expectedCoordinates);
    }
  );

  it.each([
    [
      REFERENCE_LINE_POSITION.OUTSIDE_FACE,
      { x0: 0, y0: 0, x1: 100, y1: 0 },
      [
        { x: 0, y: -10 },
        { x: 95, y: -10 },
        { x: 0, y: -20 },
        { x: 90, y: -20 },
      ],
    ],
    [
      REFERENCE_LINE_POSITION.INSIDE_FACE,
      { x0: 0, y0: -20, x1: 100, y1: -20 },
      [
        { x: 0, y: -10 },
        { x: 95, y: -10 },
        { x: 0, y: 0 },
        { x: 100, y: 0 },
      ],
    ],
    [
      REFERENCE_LINE_POSITION.CENTER,
      { x0: 0, y0: -10, x1: 100, y1: -10 },
      [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
        { x: 0, y: -20 },
        { x: 90, y: -20 },
      ],
    ],
  ])(
    'should return aux vertices sorted ascendingly by their distance to reference line',
    (referenceLine, inputVertices, expectedAuxVertices) => {
      const linePolygon = GeometryUtils.createPolygon([postProcessedLineCoords]);
      const lineProperties = { ...defaultLineProperties, referenceLine: referenceLine };
      const { updatedState: state, line: line } = getLine(inputVertices, lineProperties);
      const { auxVertices } = PostProcessor.extractCoordsAndVerticesFromPolygon(state, line.id, linePolygon);
      expect(auxVertices).toStrictEqual(expectedAuxVertices);
    }
  );
});

describe('removeIntersections', () => {
  let state;

  beforeEach(() => {
    state = getCleanMockState();
  });

  it('An L case does not generate diagonal connections due to precision issues (90º +- 1e-10)', () => {
    const hasValidCoordinatesSpy = jest.spyOn(PostProcessor, 'hasValidCoordinates');
    // Coords from a real case that generates a diagonal connection
    const FIRST_LINE_COORDS = [
      [718.0339525740835, 701.597768066226],
      [700.222939533634, 701.597768066226],
      [700.222939533634, 899.827169793803],
      [718.0339525740835, 899.827169793803],
      [718.0339525740835, 701.597768066226],
    ];

    const SECOND_LINE_COORDS = [
      [700.2229395338045, 882.0161567533535],
      [1046.4521113476135, 882.0161567566685],
      [1046.452111347443, 899.827169797118],
      [700.222939533634, 899.827169793803],
      [700.2229395338045, 882.0161567533535],
    ];

    const { updatedState, line: firstLine } = addDummyLineWithCoordinates(state, FIRST_LINE_COORDS);
    state = updatedState;

    const { updatedState: secondState, line: secondLine } = addDummyLineWithCoordinates(state, SECOND_LINE_COORDS);
    state = secondState;

    const intersectingLines = [firstLine];
    const outputPolygon = PostProcessor.removeIntersections(state, secondLine.id, intersectingLines);
    const [expectedCoordinates] = outputPolygon.geometry.coordinates;

    expect(expectedCoordinates).toHaveLength(ACCEPTED_NUMBER_OF_COORDINATES); // A different number means a different connection, eg 6 will lead into a diagonal connection
    expect(hasValidCoordinatesSpy).toHaveBeenCalled();
  });

  /**  (0, 3)           (5, 3)
   *    ┌─────────────────┐
   *    │                 │
   *    │        A        \
   *    │                / \
   *    │               /   \
   *    └───────────────\    \
   *   (0, 2)            \    \
   *                      \ B  \
   *                       \    \
   *                        \    \
   *                         \  /
   *                          \/
   *
   * The intersection is invalid because the polygon 'B' intersects the polygon 'A' such, that
   * the operation A.difference(B) computes a polygon that has too great amount of coordinates,
   * that will remain even if the 'convexHull' operation is applied.
   */
  const getInvalidLineIntersection = state => {
    const primaryLinePolygon = bboxPolygon([0, 3, 5, 2]);

    // shapely equivalent: rotate(translate(p, xoff=4, yoff=-2), -45)
    const intersectingLinePolygon = transformRotate(transformTranslate(primaryLinePolygon, 500, 90), 45, {
      pivot: [4.5, 2],
    });

    const { updatedState, line: primaryLine } = addDummyLineWithCoordinates(
      state,
      primaryLinePolygon.geometry.coordinates[0]
    );
    state = addDummyLineWithCoordinates(updatedState, intersectingLinePolygon.geometry.coordinates[0]).updatedState;
    return { primaryLine, coordinates: primaryLinePolygon.geometry.coordinates, updatedState: state };
  };

  it('should return the original line polygon if it is not valid', () => {
    const hasValidCoordinatesSpy = jest.spyOn(PostProcessor, 'hasValidCoordinates');
    const { primaryLine, coordinates, updatedState } = getInvalidLineIntersection(state);
    const layer = updatedState.scene.layers['layer-1'];
    const intersectingLines = GeometryUtils.getPostProcessableIntersectingLines(layer, primaryLine.id);
    const polygonWithoutIntersections = PostProcessor.removeIntersections(
      updatedState,
      primaryLine.id,
      intersectingLines
    );
    expect(polygonWithoutIntersections.geometry.coordinates).toStrictEqual(coordinates);
    expect(hasValidCoordinatesSpy).toHaveBeenCalled();
  });
});

describe('hasValidCoordinates', () => {
  it.each([
    [
      // linear ring
      [
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 0],
      ],
      false,
    ],
    [
      // rectangle
      [
        [0, 0],
        [0, 2],
        [1, 2],
        [1, 0],
        [0, 0],
      ],
      true,
    ],
    [
      // linear ring with duplicated coordinate
      [
        [0, 0],
        [1, 0],
        [1, 1],
        [1, 1],
        [0, 0],
      ],
      false,
    ],
    [
      // 'rectangle' with 5 edges
      [
        [0, 0],
        [0, 2],
        [1, 2],
        [1, 1],
        [1, 0],
        [0, 0],
      ],
      false,
    ],
  ])(
    `checks if the polygon has other than ${ACCEPTED_NUMBER_OF_COORDINATES} coordinates and other than ${ACCEPTED_NUMBER_OF_POLYGON_EDGES} edges`,
    (coords, expectedResult) => {
      return expect(PostProcessor.hasValidCoordinates([coords])).toBe(expectedResult);
    }
  );
});
