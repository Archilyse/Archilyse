import { MOCK_SCENE, MOCK_STATE } from '../tests/utils';
import { Hole as HoleType } from '../types';
import { GeometryUtils, SnapUtils } from '../utils/export';
import cloneDeep from '../utils/clone-deep';
import { OPENING_TYPE, REFERENCE_LINE_POSITION, SeparatorsType } from '../constants';
import {
  addHoleToState,
  addLineToState,
  getCleanMockState,
  getMockState,
  SELECTED_LAYER_ID,
} from '../tests/utils/tests-utils';
import { Hole as HoleModel } from '../models';
import Hole, { openingOverlappingOtherOpenings } from './hole';

const LAYER_ID = 'layer-1';

type Point = { x: number; y: number };

const MOCK_HOLE_COORDINATES = [
  [
    [50, 30],
    [200, 30],
    [200, 50],
    [50, 50],
    [50, 30],
  ],
];

const MOCK_SWEEPING_POINTS: HoleType['door_sweeping_points'] = {
  angle_point: [189, 40],
  closed_point: [109, 40],
  opened_point: [189, 120],
};

const mockNearestSnap = (x, y, lineID) => {
  const nearestSnapSpy = jest.spyOn(SnapUtils, 'nearestSnap');
  nearestSnapSpy.mockReturnValue({
    point: { x, y },
    snap: { metadata: { lineID } },
  });
};

const createTwoLinesWithAHoleOnTheFirst = state => {
  // Add two lines
  const lineResult = addLineToState(state, SeparatorsType.WALL, { x0: 50, y0: 50, x1: 250, y1: 50 });
  state = lineResult.updatedState;
  const lineWithHole = lineResult.line;

  const line2Result = addLineToState(state, SeparatorsType.WALL, { x0: 230, y0: 50, x1: 300, y1: 50 });
  state = line2Result.updatedState;
  const lineWithoutHole = line2Result.line;

  // Add hole to the first line
  const holeResult = addHoleToState(
    state,
    OPENING_TYPE.DOOR,
    lineWithHole.id,
    MOCK_HOLE_COORDINATES,
    MOCK_SWEEPING_POINTS
  );
  state = holeResult.updatedState;
  return { state, hole: holeResult.hole, lineWithHole, lineWithoutHole };
};

describe('Hole class, methods & aux functions', () => {
  const state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, drawingSupport: { type: 'window' } });
  const lineID = 'b3935f16-7180-4b30-ae5c-392a7f8b50e7'; // taken from mockScene.json, its a line that contains an opening
  const existingHoleID = 'c1db052f-b665-4c24-9b08-dd8efa320ce9';
  const OVERLAP_CASE_HORIZONTAL_LINE_FALSE = [{ x: 290, y: 4000 }, lineID, false];
  const OVERLAP_CASE_EXACT_LINE = [{ x: 306, y: 4115 }, lineID, true];
  const OVERLAP_CASE_NEXT_TO_LINE = [{ x: 385, y: 4247 }, lineID, false];
  const OVERLAP_CASE_CLEAR_OVERLAP = [{ x: 320, y: 4150 }, lineID, true];

  describe('openingOverlappingOtherOpenings', () => {
    it.each([
      ['A hole is placed next to each other, so there is no overlap', ...OVERLAP_CASE_HORIZONTAL_LINE_FALSE],
      ['A hole is placed exactly where the other one starts so there is an overlap', ...OVERLAP_CASE_EXACT_LINE],
      ['A hole is immediately after the other one so there is no overlap', ...OVERLAP_CASE_NEXT_TO_LINE],
      ['A hole is placed within an existing hole, so the overlap is true', ...OVERLAP_CASE_CLEAR_OVERLAP],
    ])('Check overlap when %s', (_, snapPoint: Point, lineID: string, expectedOverlap: boolean) => {
      const layer = state.scene.layers[LAYER_ID];
      const lineHolesIds: string[] = Object.values(layer.lines[lineID].holes);
      const otherHoles = lineHolesIds.map(holeID => layer.holes[holeID]);

      const overlaps = openingOverlappingOtherOpenings(state, snapPoint, lineID, existingHoleID, otherHoles);
      expect(overlaps).toBe(expectedOverlap);
    });
  });

  describe('Set properties', () => {
    it('Increase hole length properly', () => {
      const state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, drawingSupport: { type: 'window' } });
      const layer = state.scene.layers[LAYER_ID];
      const allHoles = Object.values(layer.holes) as HoleType[];
      const hole = allHoles[0];
      const getPolygonPointsSpy = jest.spyOn(Hole, 'getPolygonPoints');
      getPolygonPointsSpy.mockReturnValueOnce([
        [0, 0],
        [0, 1],
        [1, 1],
        [1, 0],
        [0, 0],
      ]);

      const newLength = hole.properties.length.value + 10;
      const newProperties = { length: { value: newLength } };

      const updatedState = Hole.setProperties(state, LAYER_ID, hole.id, newProperties).updatedState;
      const updatedHole = updatedState.scene.layers[LAYER_ID].holes[hole.id];
      expect(updatedHole.properties.length.value).toBe(newLength);
    });

    it('Length cannot be increased if the hole will overlap with another hole', () => {
      let state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, drawingSupport: { type: 'window' } }); // Add a hole to the scene
      const layer = state.scene.layers[LAYER_ID];
      const allHoles = Object.values(layer.holes) as HoleType[];
      const hole = allHoles[0];

      // Add a close hole in the same line
      const newHoleCoordinates = [
        [
          [310.7072004724965, 4119.538284997315],
          [320.45902062995987, 4210.111750063324],
          [345.3405387038511, 4207.680688908472],
          [336.5887185463877, 4118.107223842463],
          [310.7072004724965, 4119.538284997315],
        ],
      ];

      state = addHoleToState(state, hole.type, hole.line, newHoleCoordinates, null, hole.properties).updatedState;

      const originalLength = hole.properties.length.value;
      const newLength = originalLength + 20;
      const newProperties = { length: { value: newLength } };

      // The length won't increase because hole would overlap
      const updatedState = Hole.setProperties(state, LAYER_ID, hole.id, newProperties).updatedState;
      const updatedHole = updatedState.scene.layers[LAYER_ID].holes[hole.id];
      expect(updatedHole.properties.length.value).not.toBe(newLength);
      expect(updatedHole.properties.length.value).toBe(originalLength);
    });
  });

  describe('openingOverValidSeparator', () => {
    it(`only ${SeparatorsType.WALL} is a valid separator`, () => {
      const { WALL, ...otherSeparators } = SeparatorsType;

      expect(Hole.openingOverValidSeparator(WALL)).toBeTruthy();
      Object.values(otherSeparators).forEach(type => {
        expect(Hole.openingOverValidSeparator(type)).toBeFalsy();
      });
    });
  });

  describe('beginDraggingHole', () => {
    let state;
    let line;
    let holeToDrag;
    const MOCK_INITIAL_DRAGGING_POSITION = { x: 100, y: 30 };

    beforeEach(() => {
      // Add a line with a hole on it
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });
      const lineResult = addLineToState(state, SeparatorsType.WALL, { x0: 50, y0: 50, x1: 250, y1: 50 });
      line = lineResult.line;
      state = lineResult.updatedState;

      const holeResult = addHoleToState(state, OPENING_TYPE.DOOR, line.id, MOCK_HOLE_COORDINATES, MOCK_SWEEPING_POINTS);
      holeToDrag = holeResult.hole;
      state = holeResult.updatedState;
    });

    it('Changes dragging support with the dragged hole and initial position', () => {
      const { x, y } = MOCK_INITIAL_DRAGGING_POSITION;
      state = Hole.beginDraggingHole(state, SELECTED_LAYER_ID, holeToDrag.id, x, y).updatedState;
      const newDraggingSupport = state.draggingSupport;

      const EXPECTED_DRAGGING_SUPPORT = {
        holeID: holeToDrag.id,
        layerID: SELECTED_LAYER_ID,
        startPointX: x,
        startPointY: y,
      };
      expect(newDraggingSupport).toStrictEqual(EXPECTED_DRAGGING_SUPPORT);
    });

    it('Explicitly selects the hole', () => {
      const { x, y } = MOCK_INITIAL_DRAGGING_POSITION;
      state = Hole.beginDraggingHole(state, SELECTED_LAYER_ID, holeToDrag.id, x, y).updatedState;

      const newSelectedHoles = state.scene.layers[SELECTED_LAYER_ID].selected.holes;
      expect(newSelectedHoles.length).toBe(1);
      expect(newSelectedHoles[0]).toBe(holeToDrag.id);

      const updatedHole = state.scene.layers[SELECTED_LAYER_ID].holes[holeToDrag.id];
      expect(updatedHole.selected).toBe(true);
    });
  });

  describe('updateDraggingHole', () => {
    let state;
    let line;
    let originalHole;

    const MOCK_INITIAL_DRAGGING_POSITION = { x: 100, y: 30 };
    const MOCK_NEW_DRAGGING_POSITION = { x: 179.11, y: 38 };

    beforeEach(() => {
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });
      const lineResult = addLineToState(state, SeparatorsType.WALL, { x0: 50, y0: 50, x1: 250, y1: 50 });
      line = lineResult.line;
      state = lineResult.updatedState;

      // Add a hole
      const holeResult = addHoleToState(state, OPENING_TYPE.DOOR, line.id, MOCK_HOLE_COORDINATES, MOCK_SWEEPING_POINTS);
      originalHole = holeResult.hole;
      state = holeResult.updatedState;

      // Select it and start dragging it to better simulate the behaviour previous to `updateDraggingHole`
      state = Hole.select(state, SELECTED_LAYER_ID, originalHole.id).updatedState;
      const { x, y } = MOCK_INITIAL_DRAGGING_POSITION;
      state = Hole.beginDraggingHole(state, SELECTED_LAYER_ID, originalHole.id, x, y).updatedState;
    });

    afterEach(() => {
      jest.clearAllMocks();
    });

    it('Updates hole coordinates & sweeping points', () => {
      mockNearestSnap(180, 40, line.id);
      const clonedState = cloneDeep(state); // Needed to compare original vs updated

      state = Hole.updateDraggingHole(clonedState, MOCK_NEW_DRAGGING_POSITION.x, MOCK_NEW_DRAGGING_POSITION.y)
        .updatedState;
      const updatedHole = state.scene.layers[SELECTED_LAYER_ID].holes[originalHole.id];

      const updatedCoordinates = updatedHole.coordinates;
      const originalCoordinates = originalHole.coordinates;
      expect(updatedCoordinates).not.toStrictEqual(originalCoordinates);

      const updateSweepingPoints = updatedHole.door_sweeping_points;
      const originalSweepingPoints = originalHole.door_sweeping_points;
      expect(updateSweepingPoints).not.toStrictEqual(originalSweepingPoints);
    });

    it('Does nothing if there is no snap', () => {
      const nearestSnapSpy = jest.spyOn(SnapUtils, 'nearestSnap');
      nearestSnapSpy.mockReturnValue(null);

      const updatedState = Hole.updateDraggingHole(state, MOCK_NEW_DRAGGING_POSITION.x, MOCK_NEW_DRAGGING_POSITION.y)
        .updatedState;
      expect(state).toStrictEqual(updatedState);
    });

    it('If it snaps to another line, updates hole-line relationships', () => {
      // Add a new line
      const lineResult = addLineToState(state, SeparatorsType.WALL, { x0: 230, y0: 50, x1: 300, y1: 50 });
      state = lineResult.updatedState;
      const newLine = lineResult.line;
      mockNearestSnap(250, 50, newLine.id);
      state = Hole.updateDraggingHole(state, MOCK_NEW_DRAGGING_POSITION.x, MOCK_NEW_DRAGGING_POSITION.y).updatedState;
      const updatedHole = state.scene.layers[SELECTED_LAYER_ID].holes[originalHole.id];
      const updatedNewLine = state.scene.layers[LAYER_ID].lines[newLine.id];

      // The hole should contain the new line and viceversa
      expect(updatedHole.line).toBe(newLine.id);
      expect(updatedNewLine.holes.includes(updatedHole.id)).toBeTruthy();

      // And the old line should not contain the hole anymore
      expect(line.holes.includes(updatedHole.id)).toBeFalsy();
    });
  });

  describe('updateDrawingHole', () => {
    let state;
    let line;

    const MOCK_DRAWING_POSITION = { x: 179.11, y: 38 };

    beforeEach(() => {
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });
      const lineResult = addLineToState(state, SeparatorsType.WALL, { x0: 50, y0: 50, x1: 250, y1: 50 });
      line = lineResult.line;
      state = lineResult.updatedState;
      state = Hole.selectToolDrawingHole(state, OPENING_TYPE.DOOR).updatedState;
    });

    afterEach(() => {
      jest.clearAllMocks();
    });

    it('Updates hole coordinates & sweeping points', () => {
      mockNearestSnap(180, 40, line.id);

      state = Hole.updateDrawingHole(state, SELECTED_LAYER_ID, MOCK_DRAWING_POSITION.x, MOCK_DRAWING_POSITION.y)
        .updatedState;
      const originalHole = Hole.getCurrentHole(state);

      const originalCoordinates = originalHole.coordinates;
      const originalSweepingPoints = originalHole.door_sweeping_points;

      // Ensure coordinates and sweeping points are stored in the state
      expect(originalCoordinates).toBeTruthy();
      expect(originalSweepingPoints).toBeTruthy();

      // If we move the door again, the coordinates and sweeping points are updated
      mockNearestSnap(185, 45, line.id);

      state = Hole.updateDrawingHole(state, SELECTED_LAYER_ID, MOCK_DRAWING_POSITION.x + 5, MOCK_DRAWING_POSITION.y + 5)
        .updatedState;

      const updatedHole = Hole.getCurrentHole(state);
      const updatedCoordinates = updatedHole.coordinates;
      const updateSweepingPoints = updatedHole.door_sweeping_points;

      expect(updatedCoordinates).not.toStrictEqual(originalCoordinates);
      expect(updateSweepingPoints).not.toStrictEqual(originalSweepingPoints);
    });

    it('Does nothing if there is no snap', () => {
      const nearestSnapSpy = jest.spyOn(SnapUtils, 'nearestSnap');
      nearestSnapSpy.mockReturnValue(null);

      const updatedState = Hole.updateDraggingHole(state, MOCK_DRAWING_POSITION.x, MOCK_DRAWING_POSITION.y)
        .updatedState;
      expect(state).toStrictEqual(updatedState);
    });
  });

  describe('replaceLines', () => {
    it('Update hole lines relationship when moving the hole from one line to another', () => {
      let state = getCleanMockState();
      const {
        state: updatedState,
        hole,
        lineWithHole: currentLine,
        lineWithoutHole: newLine,
      } = createTwoLinesWithAHoleOnTheFirst(state);
      state = updatedState;
      state = Hole.replaceLines(state, hole.id, currentLine.id, newLine.id).updatedState;

      const updatedHole = state.scene.layers[LAYER_ID].holes[hole.id];
      const updatedNewLine = state.scene.layers[LAYER_ID].lines[newLine.id];
      // The hole should contain the new line and viceversa
      expect(updatedHole.line).toBe(newLine.id);
      expect(updatedNewLine.holes.includes(updatedHole.id)).toBeTruthy();

      // And the old line should not contain the hole anymore
      expect(currentLine.holes.includes(updatedHole.id)).toBeFalsy();
    });
  });
});

describe('updateLineAndCoordinates', () => {
  it('On a hole in the same line, keeps the same relationship and only update hole coords', () => {
    let state = getCleanMockState();
    const { state: updatedState, hole, lineWithoutHole, lineWithHole } = createTwoLinesWithAHoleOnTheFirst(state);
    state = updatedState;
    state = Hole.select(state, SELECTED_LAYER_ID, hole.id).updatedState;

    const newHolePosition = {
      point: { x: lineWithHole.coordinates[0][0][0] + 10, y: lineWithHole.coordinates[0][0][1] },
    };
    const currentHoleCoordinates = cloneDeep(hole.coordinates);
    // Same line (hole is just dragged along it on a different snap point)
    state = Hole.updateLineAndCoordinates(state, hole, lineWithHole, SELECTED_LAYER_ID, hole.id, newHolePosition)
      .updatedState;

    const updatedHole = state.scene.layers[LAYER_ID].holes[hole.id];
    const updateLineWithHole = state.scene.layers[LAYER_ID].lines[lineWithHole.id];

    // The relationship should be the same
    expect(updatedHole.line).toBe(lineWithHole.id);
    expect(updateLineWithHole.holes.includes(updatedHole.id)).toBeTruthy();

    // Line without hole still has no hole
    expect(lineWithoutHole.holes.includes(updatedHole.id)).toBeFalsy();

    // Coordinates should have been updated
    expect(currentHoleCoordinates).not.toBe(updatedHole.coordinates);
  });

  it('On a hole that was in a line and now is drawn in a new one, replace the lines', () => {
    let state = getCleanMockState();
    const {
      state: updatedState,
      hole,
      lineWithHole: oldLine,
      lineWithoutHole: newLine,
    } = createTwoLinesWithAHoleOnTheFirst(state);
    state = updatedState;
    state = Hole.select(state, SELECTED_LAYER_ID, hole.id).updatedState;

    const newHolePosition = {
      point: { x: newLine.coordinates[0][0][0] + 10, y: newLine.coordinates[0][0][1] },
    };
    // We are going to put the hole in the line previously did not have it
    state = Hole.updateLineAndCoordinates(state, hole, newLine, SELECTED_LAYER_ID, hole.id, newHolePosition)
      .updatedState;

    const updatedHole = state.scene.layers[LAYER_ID].holes[hole.id];
    const updatedNewLine = state.scene.layers[LAYER_ID].lines[newLine.id];
    // The hole should contain the new line and viceversa
    expect(updatedHole.line).toBe(newLine.id);
    expect(updatedNewLine.holes.includes(updatedHole.id)).toBeTruthy();

    // And the old line should not contain the hole anymore
    expect(oldLine.holes.includes(updatedHole.id)).toBeFalsy();
  });
});

describe('Copying openings', () => {
  it('Copying an opening should have the same properties as the opening thats being copied from', () => {
    let state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });
    const layer = state.scene.layers[LAYER_ID];

    const allHoles = Object.values(layer.holes) as HoleType[];
    const holeID = allHoles[0].id;
    const hole = layer.holes[holeID];

    state = Hole.select(state, LAYER_ID, holeID).updatedState;
    state = Hole.copySelectedHole(state).updatedState;

    let drawingSupport = state.drawingSupport;
    const properties = drawingSupport.properties;

    Object.entries(properties).forEach(([key, value]) => expect(hole.properties[key]).toStrictEqual(value));

    const x = 489.383107406264;
    const y = 5967.533840811182;

    mockNearestSnap(x, y, '4db6ed77-c27e-41c8-91b5-26fc94813982');

    const getPolygonPointsSpy = jest.spyOn(Hole, 'getPolygonPoints');
    getPolygonPointsSpy.mockReturnValueOnce([
      [0, 0],
      [0, 1],
      [1, 1],
      [1, 0],
      [0, 0],
    ]);

    state = Hole.updateDrawingHole(state, LAYER_ID, x, y).updatedState;
    drawingSupport = state.drawingSupport;

    expect(drawingSupport.properties).toEqual(properties);

    const createdHoleId = state.scene.layers[LAYER_ID].selected.holes[0];
    const createdHole = state.scene.layers[LAYER_ID].holes[createdHoleId];

    Object.entries(properties).forEach(([key, value]) => expect(createdHole.properties[key]).toStrictEqual(value));
    expect(Object.values(state.scene.layers[LAYER_ID].holes).length).toBe(2);
  });
});

describe('getPolygonPoints', () => {
  it.each([
    [
      'perpendicular line',
      { x: 0, y: 2 },
      [
        [0, 0],
        [0, 5],
      ],
      [
        [-2.5, 0.5000000000000002],
        [-2.5, 3.5],
        [2.5, 3.5],
        [2.5, 0.4999999999999998],
        [-2.5, 0.5000000000000002],
      ],
    ],
    [
      'horizontal line',
      { x: 2.5, y: 0 },
      [
        [0, 0],
        [5, 0],
      ],
      [
        [1, 2.5],
        [4, 2.5],
        [4, -2.5],
        [1, -2.5],
        [1, 2.5],
      ],
    ],
    [
      'line with a positive angle',
      { x: 2.5, y: 2.5 },
      [
        [0, 0],
        [5, 5],
      ],
      [
        [-0.32842712474618985, 3.207106781186548],
        [1.7928932188134528, 5.32842712474619],
        [5.32842712474619, 1.7928932188134523],
        [3.207106781186547, -0.32842712474618985],
        [-0.32842712474618985, 3.207106781186548],
      ],
    ],
    [
      'line with a negative angle',
      { x: 2.5, y: 2.5 },
      [
        [0, 5],
        [5, 5],
      ],
      [
        [1, 5],
        [4, 5],
        [4, 0],
        [1, 0],
        [1, 5],
      ],
    ],
  ])('works with a %s', (_, snapPoint, linePoints, EXPECTED_HOLE_POINTS) => {
    const wallThickness = 5;
    const snap = { snap: { metadata: { lineID: '1' } }, point: snapPoint };
    const vertices = linePoints.reduce((acc, [x, y], i) => {
      const id = ['v', i].join('');
      acc[id] = { id, x, y, lines: ['1'] };
      return acc;
    }, {}) as any;

    let state = MOCK_STATE;
    state = {
      ...state,
      scene: {
        ...state.scene,
        layers: {
          ...state.scene.layers,
          'layer-1': {
            ...state.scene.layers['layer-1'],
            selected: { ...state.scene.layers['layer-1'].selected, holes: ['holeA'] },
            holes: {
              ...state.scene.layers['layer-1'].holes,
              holeA: new HoleModel({ properties: { length: { value: 3 } } }),
            },
            vertices: vertices,
            lines: {
              ...state.scene.layers['layer-1'].lines,
              '1': {
                ...state.scene.layers['layer-1'].lines['1'],
                id: '1',
                vertices: Object.keys(vertices),
                holes: [],
                properties: {
                  ...state.scene.layers['layer-1'].lines['1'].properties,
                  width: {
                    ...state.scene.layers['layer-1'].lines['1'].properties.width,
                    value: wallThickness,
                  },
                  referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
                },
              },
            },
          },
        },
        selectedLayer: 'layer-1',
      },
    };
    const holePoints = Hole.getPolygonPoints(state, snap.snap.metadata.lineID, snap.point);
    expect(holePoints).toStrictEqual(EXPECTED_HOLE_POINTS);
  });
});

describe('getDoorSweepingPoints', () => {
  it.each([
    [
      false,
      false,
      [
        { x: 0, y: 0 },
        { x: 0, y: 10 },
      ],
      { angle_point: [0, 0], closed_point: [0, 10], opened_point: [-10, 0] },
    ],
    [
      false,
      true,
      [
        { x: 0, y: 0 },
        { x: 10, y: 0 },
      ],
      { angle_point: [10, 0], closed_point: [0, 0], opened_point: [10, 10] },
    ],
    [
      true,
      false,
      [
        { x: 5, y: 10 },
        { x: 10, y: 10 },
      ],
      { angle_point: [5, 10], closed_point: [10, 10], opened_point: [5, 5] },
    ],
    [
      true,
      true,
      [
        { x: 10, y: 11 },
        { x: 11, y: 11 },
      ],
      { angle_point: [11, 11], closed_point: [10, 11], opened_point: [11, 10] },
    ],
  ])(
    'sets sweeping points based on input vertices and flip parameters',
    (flipHorizontal, flipVertical, vertices, expectedSweepingPoints) => {
      const [vertex0, vertex1] = vertices;
      const sweepingPoints = Hole.getDoorSweepingPoints(vertex0, vertex1, flipHorizontal, flipVertical);
      Object.entries(sweepingPoints).forEach(([attrName, value]) => {
        expect(expectedSweepingPoints[attrName][0]).toBeCloseTo(value[0]);
        expect(expectedSweepingPoints[attrName][1]).toBeCloseTo(value[1]);
      });
    }
  );
  it.each([
    [false, false, 90],
    [false, true, -90],
    [true, false, -90],
    [true, true, 90],
  ])('rotates by the expected angle the opening point', (flipHorizontal, flipVertical, expectedRotationAngle) => {
    const rotateSpy = jest.spyOn(GeometryUtils, 'rotatePointAroundPoint');
    Hole.getDoorSweepingPoints({ x: 0, y: 0 }, { x: 1, y: 1 }, flipHorizontal, flipVertical);
    expect(rotateSpy).toHaveBeenCalledWith(
      expect.any(Number),
      expect.any(Number),
      expect.any(Number),
      expect.any(Number),
      expectedRotationAngle
    );
  });
});

describe('adjustHolePolygonAfterLineChange', () => {
  it.each([
    ['Adjusting the hole Polygon remove it if the hole is not correctly inside the wall', false, 0],
    ['Adjusting the hole Polygon does not remove it if the hole is correctly inside the wall', true, 1],
  ])('%s', (_, isValid: boolean, expectedNumber: number) => {
    const state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE, snapMask: {} });

    jest.spyOn(Hole, 'areNewPropertiesValid').mockImplementation(() => isValid);
    const holeID = 'c1db052f-b665-4c24-9b08-dd8efa320ce9';
    // When
    const response = Hole.adjustHolePolygonAfterLineChange(state, LAYER_ID, holeID);

    // Then the new state should have the hole removed
    const allHoles = Object.values(response.updatedState.scene.layers[LAYER_ID].holes);
    expect(allHoles.length).toBe(expectedNumber);
  });
});
