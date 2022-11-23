import { MOCK_SCENE, MOCK_STATE } from '../tests/utils';
import { cloneDeep, PostProcessor, SnapUtils } from '../utils/export';
import {
  MIN_WALL_LENGTH_IN_CM,
  MODE_DRAWING_LINE,
  MODE_IDLE,
  OPENING_TYPE,
  REFERENCE_LINE_POSITION,
  SeparatorsType,
  SNAPS,
} from '../constants';
import MyCatalog from '../catalog-elements/mycatalog';
import { addHoleToState, addLineToState, getCleanMockState, getMockState } from '../tests/utils/tests-utils';
import { getSelectedLayer } from '../utils/state-utils';
import { State } from '../types';
import { Line, Project } from './export';

const LAYER_ID = MOCK_STATE.scene.selectedLayer;

const mockStateAndLineWithAuxVertices = (auxVertices, layerId, lineId) => {
  const STATE = cloneDeep(MOCK_STATE);
  const layer = STATE.scene.layers[layerId];
  const line = layer.lines[lineId];
  line.referenceLine = REFERENCE_LINE_POSITION.CENTER;
  line.auxVertices = auxVertices;
  for (const v of auxVertices) {
    layer.vertices[v] = { id: v, x: 1, y: 1, lines: [lineId], areas: [] };
  }

  layer.selected.lines = [lineId];
  layer.selected.vertices = auxVertices;
  return { state: STATE, line };
};

const mockStateWithArea = (separatorType, width) => {
  const properties = {
    referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
    width: { value: width },
  };

  const points = [
    [
      [0, 0],
      [0, 50],
    ],
    [
      [0, 50],
      [50, 50],
    ],
    [
      [50, 50],
      [50, 0],
    ],
    [
      [50, 0],
      [0, 0],
    ],
  ];

  let state = getCleanMockState();

  points.forEach(([[x1, y1], [x2, y2]]) => {
    state = Line.createAvoidingIntersections(state, LAYER_ID, separatorType, x1, y1, x2, y2, properties).updatedState;
  });

  return state;
};

describe('Line class methods', () => {
  let state;

  beforeEach(() => {
    state = getCleanMockState();
  });

  it('Ending drawing a line adds a line to the state', async () => {
    const BEGIN_COORDINATES = [0, 0];
    const END_COORDINATES = [150, 0];

    state = Line.selectToolDrawingLine(state, 'wall').updatedState;

    const selectedLayer = state.scene.selectedLayer;

    let allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_BEFORE_DRAW = allLines.length;

    state = Line.beginDrawingLine(state, selectedLayer, ...BEGIN_COORDINATES).updatedState;
    state = Line.updateDrawingLine(state, ...END_COORDINATES).updatedState;
    state = Line.endDrawingLine(state, ...END_COORDINATES).updatedState;

    allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_AFTER_DRAW = allLines.length;

    expect(LINES_AFTER_DRAW).toBeGreaterThan(LINES_BEFORE_DRAW);
  });

  it(`Ending drawing a line smaller than ${MIN_WALL_LENGTH_IN_CM} cm does not add a line to the state`, async () => {
    const BEGIN_COORDINATES = [0, 0];
    const END_COORDINATES = [3, 0];

    state = Line.selectToolDrawingLine(state, 'wall').updatedState;

    const selectedLayer = state.scene.selectedLayer;

    let allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_BEFORE_DRAW = allLines.length;

    state = Line.beginDrawingLine(state, selectedLayer, ...BEGIN_COORDINATES).updatedState;
    state = Line.updateDrawingLine(state, ...END_COORDINATES).updatedState;
    state = Line.endDrawingLine(state, ...END_COORDINATES).updatedState;

    allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_AFTER_DRAW = allLines.length;

    expect(LINES_AFTER_DRAW).toEqual(LINES_BEFORE_DRAW);
  });

  it(`Ending drawing a small line from another line does not snap to it and is added to the state`, async () => {
    // Start on an existing vertex
    const { vertices } = MOCK_STATE.scene.layers[LAYER_ID];
    const [v0]: any = Object.values(vertices);
    const DISTANCE = 5; // The snap radius is 10 by default, so normally the new line would snap to the connected line and not be created
    const BEGIN_COORDINATES = [v0.x, v0.y];
    const END_COORDINATES = [v0.x + DISTANCE, v0.y];

    state = {
      ...state,
      snapMask: { SNAP_POINT: true, SNAP_SEGMENT: false },
    };
    state = Line.selectToolDrawingLine(state, 'wall').updatedState;

    const selectedLayer = state.scene.selectedLayer;

    let allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_BEFORE_DRAW = allLines.length;
    state = Line.beginDrawingLine(state, selectedLayer, ...BEGIN_COORDINATES).updatedState;

    // Mock snap elements to starting vertex
    state = {
      ...state,
      snapElements: [
        new SnapUtils.PointSnap({
          type: 'point',
          x: v0.x,
          y: v0.y,
          radius: SNAPS.POINT.RADIUS,
          priority: SNAPS.POINT.PRIORITY,
          metadata: {},
        }),
      ],
    };

    // Finish drawing the line
    state = Line.updateDrawingLine(state, ...END_COORDINATES).updatedState;
    state = Line.endDrawingLine(state, ...END_COORDINATES).updatedState;

    // Expect line to be created
    allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const LINES_AFTER_DRAW = allLines.length;
    expect(LINES_AFTER_DRAW).toEqual(LINES_BEFORE_DRAW + 1);
  });

  it.each([[SeparatorsType.WALL], [SeparatorsType.COLUMN], [SeparatorsType.RAILING], [SeparatorsType.AREA_SPLITTER]])(
    'While drawing a %s prototype, all the vertices are unique but when drawing is finished the common vertices are merged except for the area splitters',
    linePrototype => {
      const START = { x: 0, y: 0 };
      const END = { x: 100, y: 0 };

      // First we're drawing one line, so we can intersect with it later
      state = Line.selectToolDrawingLine(state, linePrototype).updatedState;
      state = Line.beginDrawingLine(state, LAYER_ID, START.x, START.y).updatedState;
      state = Line.updateDrawingLine(state, END.x, END.y).updatedState;
      state = Line.endDrawingLine(state, END.x, END.y).updatedState;
      let allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const firstLine = allLines[0];
      const firstLineVertices = firstLine.vertices.concat(firstLine.auxVertices);

      // Now we'll draw a second line, starting from where the first one ended
      state = Line.selectToolDrawingLine(state, linePrototype).updatedState;
      state = Line.beginDrawingLine(state, LAYER_ID, END.x, END.y).updatedState;
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const secondLine = allLines[allLines.length - 1]; // last

      // While drawing, the common vertices are ignored and they're always unique
      for (let i = 0; i < 5; i++) {
        END.x += 20;
        END.y += 20;

        state = Line.updateDrawingLine(state, END.x, END.y).updatedState;
        const updatedSecondLine = state.scene.layers[LAYER_ID].lines[secondLine.id];
        const newVertices = updatedSecondLine.vertices.concat(updatedSecondLine.auxVertices);
        const hasCommonVertex = newVertices.some(vertexID => firstLineVertices.includes(vertexID));
        expect(hasCommonVertex).toBeFalsy();
      }

      // And when the drawing is finished, the common vertices are merged except for the area splitters
      state = Line.endDrawingLine(state, END.x, END.y).updatedState;
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const createdLine = allLines[allLines.length - 1]; // last
      const createdLineVertices = createdLine.vertices.concat(createdLine.auxVertices);
      const hasCommonVertex = createdLineVertices.some(vertexID => firstLineVertices.includes(vertexID));

      if (linePrototype === SeparatorsType.AREA_SPLITTER) {
        expect(hasCommonVertex).toBeFalsy();
      } else {
        expect(hasCommonVertex).toBeTruthy();
      }
    }
  );

  it.each([
    [SeparatorsType.WALL, 5],
    [SeparatorsType.COLUMN, 5],
    [SeparatorsType.RAILING, 5],
    [SeparatorsType.AREA_SPLITTER, 1],
  ])(
    'When removing a %s, the prototype is properly removed from the state and also there are no orphan vertices left in the state',
    (separatorType, width) => {
      state = mockStateWithArea(separatorType, width);

      let layer = state.scene.layers[LAYER_ID];
      let vertices = Object.values(layer.vertices);
      let lines = Object.values(layer.lines) as any;

      let LINES_COUNT = lines.length;
      let VERTICES_COUNT = vertices.length;

      lines.forEach(line => {
        const lineID = line.id;
        const allVertices = line.vertices.concat(line.auxVertices).map(vertexID => layer.vertices[vertexID]);
        const commonVertices = allVertices.filter(vertex => vertex.lines.length > 1);
        const EXPECTED_REMOVED_VERTICES_COUNT = allVertices.length - commonVertices.length;
        state = Line.remove(state, LAYER_ID, lineID).updatedState;
        layer = state.scene.layers[LAYER_ID];
        vertices = Object.values(layer.vertices);
        lines = Object.values(layer.lines) as any;

        expect(lines.length).toBe(LINES_COUNT - 1);
        expect(vertices.length).toBe(VERTICES_COUNT - EXPECTED_REMOVED_VERTICES_COUNT);

        LINES_COUNT = lines.length;
        VERTICES_COUNT = vertices.length;

        commonVertices.forEach(vertex => {
          const updatedVertex = layer.vertices[vertex.id];
          expect(updatedVertex.lines.includes(lineID)).toBeFalsy();
        });
      });

      expect(lines.length === 0).toBeTruthy();
      expect(vertices.length === 0).toBeTruthy();
    }
  );

  describe('Aux line vertices', () => {
    const LINE_ID = Object.keys(MOCK_STATE.scene.layers[LAYER_ID].lines)[0];
    const MAIN_VERTICES = [
      { x: 385, y: 943 },
      { x: 730, y: 943 },
    ];
    const WIDTH = 20;

    const EXPECTED_COORDS_CENTER = [
      { x: 385, y: 953 },
      { x: 730, y: 953 },
      { x: 385, y: 933 },
      { x: 730, y: 933 },
    ];
    const EXPECTED_COORDS_OUTSIDE_FACE = [
      { x: 385, y: 933 },
      { x: 730, y: 933 },
      { x: 385, y: 923 },
      { x: 730, y: 923 },
    ];
    const EXPECTED_COORDS_INSIDE_FACE = [
      { x: 385, y: 953 },
      { x: 730, y: 953 },
      { x: 385, y: 963 },
      { x: 730, y: 963 },
    ];

    const EXPECTED_COORDS_INCREASED_WIDTH = [
      { x: 385, y: 963 },
      { x: 730, y: 963 },
      { x: 385, y: 983 },
      { x: 730, y: 983 },
    ];

    it.each([
      [REFERENCE_LINE_POSITION.CENTER, WIDTH, EXPECTED_COORDS_CENTER],
      [REFERENCE_LINE_POSITION.OUTSIDE_FACE, WIDTH, EXPECTED_COORDS_OUTSIDE_FACE],
      [REFERENCE_LINE_POSITION.INSIDE_FACE, WIDTH, EXPECTED_COORDS_INSIDE_FACE],
      [REFERENCE_LINE_POSITION.INSIDE_FACE, WIDTH + 20, EXPECTED_COORDS_INCREASED_WIDTH],
    ])('Create aux vertices with a reference line: %s and width: %s', (referenceLine, width, expectedCoords) => {
      const lineProperties = {
        width: { value: width },
        referenceLine: referenceLine,
      };
      const { auxVertices } = Line.createAuxVertices(state, MAIN_VERTICES, lineProperties, LAYER_ID, LINE_ID);

      const newAuxVertices = auxVertices.map(v => v);
      expect(newAuxVertices.length).toBe(4);
      auxVertices.forEach((vertex, index) => {
        const { x, y } = vertex;
        expect(x).toBe(expectedCoords[index].x);
        expect(y).toBe(expectedCoords[index].y);
      });
    });

    it('Update the aux vertices of a line when changing the reference line', () => {
      const AUX_VERTICES = ['v3', 'v4', 'v5', 'v6'];
      const EXPECTED_UPDATED_COORDS = [
        { x: 8.071067811865, y: -5.071067811865 },
        { x: 9.071067811865, y: -4.071067811865 },
        { x: 15.142135623731, y: -12.142135623731 },
        { x: 16.142135623731, y: -11.142135623731 },
      ];

      const { state: STATE, line } = mockStateAndLineWithAuxVertices(AUX_VERTICES, LAYER_ID, LINE_ID);
      const newProperties = {
        width: { value: WIDTH },
        referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
      };
      const { updatedState } = Line.updateLineAuxVertices(getMockState(STATE), newProperties, line, LAYER_ID, LINE_ID);

      const newState = updatedState;
      const newLayer = newState.scene.layers[LAYER_ID];
      const newVerticesIds = Object.keys(newLayer.vertices);
      const newAuxVerticesIds = newLayer.lines[LINE_ID].auxVertices;

      // Original aux vertices have been removed
      for (const originalVertex of AUX_VERTICES) {
        expect(newVerticesIds.includes(originalVertex)).not.toBe(true);
        expect(newAuxVerticesIds.includes(originalVertex)).not.toBe(true);
      }
      // And we have 4 more new ones with the expected coords
      expect(newAuxVerticesIds.length).toBe(4);
      newAuxVerticesIds.forEach((newVertexId, index) => {
        const auxVertex = newLayer.vertices[newVertexId];
        expect(auxVertex.x).toBe(EXPECTED_UPDATED_COORDS[index].x);
        expect(auxVertex.y).toBe(EXPECTED_UPDATED_COORDS[index].y);
      });
    });

    it('Updating the aux vertices of a line unselects the previously selected vertices', () => {
      const AUX_VERTICES = ['v3', 'v4', 'v5', 'v6'];
      const { state: STATE, line } = mockStateAndLineWithAuxVertices(AUX_VERTICES, LAYER_ID, LINE_ID);
      const newProperties = {
        width: { value: WIDTH },
        referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
      };

      const { updatedState } = Line.updateLineAuxVertices(getMockState(STATE), newProperties, line, LAYER_ID, LINE_ID);

      const newState = updatedState;
      const newSelectedVertices = newState.scene.layers[LAYER_ID].selected.vertices;
      newSelectedVertices.forEach(vertexID => {
        expect(AUX_VERTICES.includes(vertexID)).toBeFalsy();
      });
    });
  });

  describe('Reference lines', () => {
    const LINE1 = [
      { x: 400, y: 1901 },
      { x: 800, y: 1901 },
    ];
    const LINE2 = [
      { x: 800, y: 1901 },
      { x: 800, y: 1600 },
    ];

    it('Line should inherit reference line from the starting line when in idle mode', () => {
      state = Line.selectToolDrawingLine(state, 'wall').updatedState;

      // Draw the first line
      state = Line.beginDrawingLine(state, LAYER_ID, LINE1[0].x, LINE1[0].y).updatedState;
      let allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const line = allLines[0];
      const defaultReferenceLine = line.properties.referenceLine;
      state = Line.changeReferenceLine(state).updatedState;
      state = Line.updateDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;

      // Check if the created line reference line has updated
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const firstLine = allLines[0];
      const firstLineReferenceLine = firstLine.properties.referenceLine;
      expect(defaultReferenceLine).not.toEqual(firstLineReferenceLine);

      // Trigger rollback to exit drawing mode
      state = Project.rollback(state).updatedState;

      // Draw the second line
      state = Line.selectToolDrawingLine(state, 'wall').updatedState;
      state = Line.beginDrawingLine(state, LAYER_ID, LINE2[0].x, LINE2[0].y).updatedState;
      state = Line.updateDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;

      // Check if reference lines of Line1 and Line2 are the same
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const secondLine = allLines[allLines.length - 1];
      const secondLineReferenceLine = secondLine.properties.referenceLine;
      expect(firstLineReferenceLine).toEqual(secondLineReferenceLine);
    });

    it('Line should inherit reference line from the previous line when in drawing mode', () => {
      // Draw the first line
      state = Line.selectToolDrawingLine(state, 'wall').updatedState;
      state = Line.beginDrawingLine(state, LAYER_ID, LINE1[0].x, LINE1[0].y).updatedState;
      let allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const line = allLines[0];
      const defaultReferenceLine = line.properties.referenceLine;
      state = Line.changeReferenceLine(state).updatedState;
      state = Line.updateDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;

      // Check if the created line reference line has updated
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const firstLine = allLines[0];
      const firstLineReferenceLine = firstLine.properties.referenceLine;
      expect(defaultReferenceLine).not.toEqual(firstLineReferenceLine);

      // Draw the second line without exiting drawing mode
      state = Line.beginDrawingLine(state, LAYER_ID, LINE2[0].x, LINE2[0].y).updatedState;
      state = Line.updateDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;

      // Check if reference lines of Line1 and Line2 are the same
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const secondLine = allLines[allLines.length - 1]; // last
      const secondLineReferenceLine = secondLine.properties.referenceLine;
      expect(firstLineReferenceLine).toEqual(secondLineReferenceLine);
    });

    it('Area splitter should NOT inherit reference line from the starting line when in idle mode', () => {
      state = Line.selectToolDrawingLine(state, 'wall').updatedState;

      // Draw the first line
      state = Line.beginDrawingLine(state, LAYER_ID, LINE1[0].x, LINE1[0].y).updatedState;
      let allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const line = allLines[0];
      const defaultReferenceLine = line.properties.referenceLine;
      state = Line.changeReferenceLine(state).updatedState;
      state = Line.updateDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE1[1].x, LINE1[1].y).updatedState;

      // Check if the created line reference line has updated
      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const firstLine = allLines[0];
      const firstLineReferenceLine = firstLine.properties.referenceLine;
      expect(defaultReferenceLine).not.toEqual(firstLineReferenceLine);

      // Trigger rollback to exit drawing mode
      state = Project.rollback(state).updatedState;

      // Draw the second line
      state = Line.selectToolDrawingLine(state, 'area_splitter').updatedState;
      state = Line.beginDrawingLine(state, LAYER_ID, LINE2[0].x, LINE2[0].y).updatedState;
      state = Line.updateDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;
      state = Line.endDrawingLine(state, LINE2[1].x, LINE2[1].y).updatedState;

      allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const areaSplitter = allLines[allLines.length - 1]; // last
      const areaSplitterReferenceLine = areaSplitter.properties.referenceLine;
      expect(areaSplitterReferenceLine).toEqual(REFERENCE_LINE_POSITION.OUTSIDE_FACE);
    });
  });

  describe('replaceVertices', () => {
    const getLineAndVerticesToReplace = (state, verticesType) => {
      const allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const line = allLines[0];
      const firstLineVertexID = line[verticesType][0];

      const vertexToReplace = state.scene.layers[LAYER_ID].vertices[firstLineVertexID];
      const allVertices = Object.values(state.scene.layers[LAYER_ID].vertices) as any;
      const newVertex = allVertices[allVertices.length - 1];
      return { line, vertexToReplace, newVertex };
    };

    beforeEach(() => {
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE });
    });
    it('Replaces one main vertex with another vertex in the same line', () => {
      const { line, newVertex, vertexToReplace } = getLineAndVerticesToReplace(state, 'vertices');

      state = Line.replaceVertices(state, LAYER_ID, line.id, newVertex, vertexToReplace).updatedState;

      const updatedLine = state.scene.layers[LAYER_ID].lines[line.id];
      const hasNewVertex = updatedLine.vertices.includes(newVertex.id);
      const hasVertexToReplace = updatedLine.vertices.includes(vertexToReplace.id);

      expect(hasNewVertex).toBeTruthy();
      expect(hasVertexToReplace).toBeFalsy();
    });

    it('Replaces one aux vertex with another in the same line', () => {
      const { line, newVertex, vertexToReplace } = getLineAndVerticesToReplace(state, 'auxVertices');

      state = Line.replaceVertices(state, LAYER_ID, line.id, newVertex, vertexToReplace).updatedState;

      const updatedLine = state.scene.layers[LAYER_ID].lines[line.id];
      const hasNewAuxVertex = updatedLine.auxVertices.includes(newVertex.id);
      const hasAuxVertexToReplace = updatedLine.auxVertices.includes(vertexToReplace.id);

      expect(hasNewAuxVertex).toBeTruthy();
      expect(hasAuxVertexToReplace).toBeFalsy();
    });
  });

  const MOCK_INITIAL_LINE_PROPERTIES = {
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

  const addLineWithHoleToState = state => {
    const MOCK_LINE_POINTS = {
      x0: 427,
      y0: 1309,
      x1: 755,
      y1: 1309,
    };
    const INITIAL_HOLE_COORDINATES = [
      [
        [620.5, 1319],
        [710.5, 1319],
        [710.5, 1299],
        [620.5, 1299],
        [620.5, 1319],
      ],
    ];

    const lineResult = addLineToState(
      state,
      SeparatorsType.WALL,
      { ...MOCK_LINE_POINTS },
      MOCK_INITIAL_LINE_PROPERTIES
    );
    state = lineResult.updatedState;
    const line = lineResult.line;

    const holeResult = addHoleToState(state, OPENING_TYPE.WINDOW, line.id, INITIAL_HOLE_COORDINATES, null);
    state = holeResult.updatedState;
    const hole = holeResult.hole;
    return { updatedState: state, line, hole };
  };

  describe('updateProperties', () => {
    beforeEach(() => {
      state = getCleanMockState();
    });

    it('Updates the properties only for those keys that exist in the state', () => {
      const recreateLineSpy = jest.spyOn(Line, 'recreateLineShape');
      const lineResult = addLineToState(
        state,
        SeparatorsType.WALL,
        { x0: 10, y0: 10, x1: 100, y1: 100 },
        MOCK_INITIAL_LINE_PROPERTIES
      );
      state = lineResult.updatedState;
      const line = lineResult.line;

      const newProperties = { referenceLine: REFERENCE_LINE_POSITION.CENTER, unknownAttribute: 123 };
      const clonedState = cloneDeep(state); // As class method will modify it, otherwise comparison below will fail
      state = Line.updateProperties(clonedState, LAYER_ID, line.id, newProperties).updatedState;

      const updatedLine = state.scene.layers[LAYER_ID].lines[line.id];
      expect(updatedLine.properties.referenceLine).toBe(REFERENCE_LINE_POSITION.CENTER);
      expect(updatedLine.properties.unknownAttribute).toBeUndefined();
      expect(updatedLine.properties.unknownAttribute).toBeFalsy();

      const sceneHistory = state.sceneHistory;
      expect(sceneHistory.last.layers).toStrictEqual(lineResult.updatedState.scene.layers);

      expect(recreateLineSpy).toHaveBeenCalled();
    });
  });

  describe('setProperties', () => {
    beforeEach(() => {
      state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE });
    });

    it('Set properties properly', () => {
      const recreateLineSpy = jest.spyOn(Line, 'recreateLineShape');
      const lineResult = addLineToState(
        state,
        SeparatorsType.WALL,
        { x0: 10, y0: 10, x1: 100, y1: 100 },
        MOCK_INITIAL_LINE_PROPERTIES
      );
      state = lineResult.updatedState;
      const line = lineResult.line;

      const newProperties = { referenceLine: REFERENCE_LINE_POSITION.CENTER };
      const clonedState = cloneDeep(state); // As class method will modify it, otherwise comparison below will fail
      state = Line.setProperties(clonedState, LAYER_ID, line.id, newProperties).updatedState;

      const updatedLine = state.scene.layers[LAYER_ID].lines[line.id];
      expect(updatedLine.properties.referenceLine).toBe(REFERENCE_LINE_POSITION.CENTER);

      const sceneHistory = state.sceneHistory;
      expect(sceneHistory.last.layers).toStrictEqual(lineResult.updatedState.scene.layers);

      expect(recreateLineSpy).toHaveBeenCalled();
    });

    it('Changing the width of a line with a hole using the form recalculates hole coordinates', () => {
      const recreateLineShapeSpy = jest.spyOn(Line, 'recreateLineShape');
      const EXPECTED_HOLE_COORDINATES = [
        [
          [620.5, 1309],
          [710.5, 1309],
          [710.5, 1269],
          [620.5, 1269],
          [620.5, 1309],
        ],
      ];
      const { updatedState, line, hole } = addLineWithHoleToState(state);
      state = updatedState;

      const newProperties = { width: { value: 40, unit: 'cm' } };
      state = Line.setProperties(state, LAYER_ID, line.id, newProperties).updatedState;

      const updatedHole = state.scene.layers[LAYER_ID].holes[hole.id];
      const updatedCoordinates = updatedHole.coordinates;
      expect(updatedCoordinates).toStrictEqual(EXPECTED_HOLE_COORDINATES);
      expect(recreateLineShapeSpy).toHaveBeenCalled();
    });
  });

  describe('updateWidthSelectedWalls', () => {
    it('Changing the width of a line with a hole using shortcuts recalculates hole coordinates', () => {
      const recreateLineShapeSpy = jest.spyOn(Line, 'recreateLineShape');
      const EXPECTED_HOLE_COORDINATES = [
        [
          [620.5, 1309],
          [710.5, 1309],
          [710.5, 1288],
          [620.5, 1288],
          [620.5, 1309],
        ],
      ];
      const { updatedState, line, hole } = addLineWithHoleToState(state);
      state = updatedState;

      // the line has to be selected in order for the width change to be applied

      const stateBeforeUpdatingWidth = cloneDeep(state); // As class method will modify it, otherwise comparison below will fail
      stateBeforeUpdatingWidth.scene.layers[LAYER_ID].lines[line.id].selected = true;
      state = Line.updateWidthSelectedWalls(cloneDeep(stateBeforeUpdatingWidth), 1).updatedState;

      const updatedHole = state.scene.layers[LAYER_ID].holes[hole.id];
      const updatedCoordinates = updatedHole.coordinates;
      expect(updatedCoordinates).toStrictEqual(EXPECTED_HOLE_COORDINATES);
      expect(recreateLineShapeSpy).toHaveBeenCalled();

      const sceneHistory = state.sceneHistory;
      expect(sceneHistory.last.layers).toStrictEqual(stateBeforeUpdatingWidth.scene.layers);
    });
  });
});

describe('Line coords calculation', () => {
  it('AddOrUpdateReferenceLineCoords generates line coordinates with outside face reference and points from left to right', async () => {
    let mockState = MOCK_STATE as State;
    const lineID = '1';
    const wallWidth = 2;
    mockState = {
      ...mockState,
      scene: {
        ...mockState.scene,
        layers: {
          ...mockState.scene.layers,
          ['layer-1']: {
            ...mockState.scene.layers['layer-1'],
            selected: { ...mockState.scene.layers['layer-1'].selected, holes: ['holeA'], lines: [lineID] },
            vertices: {
              ...mockState.scene.layers['layer-1'].vertices,
              a: { ...mockState.scene.layers['layer-1'].vertices.a, id: 'a', x: 0, y: 0, lines: [lineID] },
              b: { ...mockState.scene.layers['layer-1'].vertices.b, id: 'b', x: 5, y: 0, lines: [lineID] },
            },
            lines: {
              ...mockState.scene.layers['layer-1'].lines,
              [lineID]: {
                ...mockState.scene.layers['layer-1'].lines[lineID],
                id: lineID,
                vertices: ['a', 'b'],
                properties: {
                  ...mockState.scene.layers['layer-1'].lines[lineID].properties,
                  referenceLine: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
                  width: {
                    ...mockState.scene.layers['layer-1'].lines[lineID].properties.width,
                    value: wallWidth,
                  },
                },
              },
            },
          },
        },
      },
    };

    mockState = getMockState({ ...mockState, catalog: MyCatalog });
    const updatedState = Line.AddOrUpdateReferenceLineCoords(mockState, lineID).updatedState;
    const updatedLine = updatedState.scene.layers['layer-1'].lines[lineID];
    expect(updatedLine.coordinates).toStrictEqual([
      [
        [0, -wallWidth],
        [5, -wallWidth],
        [5, 0],
        [0, 0],
        [0, -wallWidth],
      ],
    ]);
  });
  it.each([2, 37])(
    'AddOrUpdateReferenceLineCoords generates line coordinates with inside face reference and points from rigth to left with %s cms',
    async wallWidth => {
      let mockState = MOCK_STATE;
      const lineID = '1';
      mockState = {
        ...mockState,
        scene: {
          ...mockState.scene,
          layers: {
            ...mockState.scene.layers,
            ['layer-1']: {
              ...mockState.scene.layers['layer-1'],
              selected: { ...mockState.scene.layers['layer-1'].selected, holes: ['holeA'], lines: [lineID] },
              vertices: {
                ...mockState.scene.layers['layer-1'].vertices,
                a: { ...mockState.scene.layers['layer-1'].vertices.a, id: 'a', x: 5, y: 0, lines: [lineID] },
                b: { ...mockState.scene.layers['layer-1'].vertices.b, id: 'b', x: 0, y: 0, lines: [lineID] },
              },
              lines: {
                ...mockState.scene.layers['layer-1'].lines,
                [lineID]: {
                  ...mockState.scene.layers['layer-1'].lines[lineID],
                  id: lineID,
                  vertices: ['a', 'b'],
                  properties: {
                    ...mockState.scene.layers['layer-1'].lines[lineID].properties,
                    referenceLine: REFERENCE_LINE_POSITION.INSIDE_FACE,
                    width: {
                      ...mockState.scene.layers['layer-1'].lines[lineID].properties.width,
                      value: wallWidth,
                    },
                  },
                },
              },
            },
          },
        },
      };
      mockState = getMockState({ ...mockState, catalog: MyCatalog });
      const updatedState = Line.AddOrUpdateReferenceLineCoords(mockState, lineID).updatedState;
      const updatedLine = updatedState.scene.layers['layer-1'].lines[lineID];
      expect(updatedLine.coordinates).toStrictEqual([
        [
          [0, wallWidth],
          [5, wallWidth],
          [5, 0],
          [0, 0],
          [0, wallWidth],
        ],
      ]);
    }
  );
});

describe('recreateLineShape', () => {
  let state;
  beforeEach(() => {
    state = getCleanMockState();
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
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
  const getStateWithThreeIntersectingLines = state => {
    /**
     * 3 line segments connected in a U-shape
     *
     *  (0, 100) │          │ (100, 100)
     *           |          │
     *           │          │
     *           │          │
     *           │          │
     *           └──────────┘
     *       (0, 0)        (100, 0)
     */
    state = addLineToState(state, SeparatorsType.WALL, { x0: 0, y0: 0, x1: 0, y1: 100 }, defaultLineProperties)
      .updatedState;
    const propsInsideLine = { ...defaultLineProperties, referenceLine: REFERENCE_LINE_POSITION.INSIDE_FACE };
    const middleLineWithState = addLineToState(
      state,
      SeparatorsType.WALL,
      { x0: 0, y0: 0, x1: 100, y1: 0 },
      propsInsideLine
    );
    state = addLineToState(
      middleLineWithState.updatedState,
      SeparatorsType.WALL,
      { x0: 100, y0: 0, x1: 100, y1: 100 },
      propsInsideLine
    ).updatedState;
    return { updatedState: state, middleLineID: middleLineWithState.line.id };
  };
  it.each([
    [MODE_IDLE, 6, 2],
    [MODE_DRAWING_LINE, 4, 0],
  ])('triggers postprocessing based on mode', (mode, expectedUpdatecoordsCount, expectedPostProcessLinesCount) => {
    const postprocessLineSpy = jest.spyOn(PostProcessor, 'postprocessLines');
    const updatedAuxLineVerticesSpy = jest.spyOn(Line, 'updateLineAuxVertices');
    const updateRefLineCoordsSpy = jest.spyOn(Line, 'AddOrUpdateReferenceLineCoords');
    state = {
      ...state,
      mode,
    };

    // +1 AddOrUpdateReferenceLineCoords call for each line being created
    const stateAndLineID = getStateWithThreeIntersectingLines(state);
    state = stateAndLineID.updatedState;

    const selectedLayer = getSelectedLayer(state.scene);
    state = Line.recreateLineShape(state, selectedLayer.id, stateAndLineID.middleLineID);

    expect(postprocessLineSpy).toHaveBeenCalledTimes(expectedPostProcessLinesCount);
    expect(updatedAuxLineVerticesSpy).toHaveBeenCalledTimes(1);
    expect(updateRefLineCoordsSpy).toHaveBeenCalledTimes(expectedUpdatecoordsCount);
  });
});
