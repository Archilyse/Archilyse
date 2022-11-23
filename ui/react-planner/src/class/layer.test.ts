import { MOCK_SCENE, MOCK_STATE } from '../tests/utils';
import { cloneDeep } from '../utils/export';
import { Vertex as VertexModel } from '../models';
import { PrototypesEnum, REFERENCE_LINE_POSITION, SeparatorsType } from '../constants';
import { addLineToState, getCleanMockState, getMockState } from '../tests/utils/tests-utils';
import testCases from './layer.testCases';
import { Area, Hole, Item, Layer, Line } from './export';

const LAYER_ID = MOCK_STATE.scene.selectedLayer;

type AreaTestCase = {
  input: { x0: number; y0: number; x1: number; y1: number }[];
  expectedOutput: {
    nrOfAreas: number;
    coordsByArea: {
      [key: number]: number[][][];
    };
  };
};

describe('Layer class methods', () => {
  describe('removeOrphanLinesAndVertices', () => {
    const BASE_CASE = {
      vertices: {
        a: new VertexModel({ id: 'a', prototype: PrototypesEnum.VERTICES, x: 1, y: 2, lines: ['1', '2-nonexistent'] }),
        b: new VertexModel({ id: 'b', prototype: PrototypesEnum.VERTICES, x: 3, y: 4, lines: ['1'] }),
        c: new VertexModel({ id: 'c', prototype: PrototypesEnum.VERTICES, x: 5, y: 6, lines: ['3-nonexistent'] }),
      },
      id: 'layer-1',
      lines: { '1': { id: '1', vertices: ['a', 'b'], auxVertices: [], holes: [] } },
      selected: { lines: [], vertices: [] },
    };
    it('Removes Orphan Lines refences and Orphan vertices', () => {
      const STATE = cloneDeep(MOCK_STATE);
      STATE.scene.layers[LAYER_ID] = BASE_CASE;
      const newState = Layer.removeOrphanLinesAndVertices(STATE, LAYER_ID).updatedState;
      const { vertices } = newState.scene.layers[LAYER_ID];
      expect(vertices.c).toBeFalsy();
      expect(vertices.a.lines.includes('2-nonexistent')).toBeFalsy();
    });
  });

  describe('removeLinesWithZeroLength', () => {
    const BASE_CASE = {
      vertices: {
        a: { id: '1', prototype: 'vertex', x: 1, y: 2, lines: ['1'], areas: [] },
        b: { id: '2', prototype: 'vertex', x: 3, y: 4, lines: ['1'], areas: [] },
      },
      id: 'layer-1',
      lines: { '1': { id: '1', vertices: ['a', 'b'], auxVertices: [], holes: [] } },
      selected: { lines: [], vertices: [] },
    };

    const CASE_0 = { ...BASE_CASE };
    CASE_0.vertices.a = { ...BASE_CASE.vertices.a, ...{ x: 1, y: 1 } };
    CASE_0.vertices.b = { ...BASE_CASE.vertices.b, ...{ x: 1, y: 1 } };

    const CASE_ALMOST_0 = { ...BASE_CASE };
    CASE_ALMOST_0.vertices.a = { ...BASE_CASE.vertices.a, ...{ x: 1, y: 1 } };
    CASE_ALMOST_0.vertices.b = { ...BASE_CASE.vertices.b, ...{ x: 1.0001, y: 1 } };

    const CASE_SAME_ID = { ...BASE_CASE };
    CASE_SAME_ID.vertices.a = { ...BASE_CASE.vertices.a, ...{ x: 1, y: 2, id: 'payaso' } };
    CASE_SAME_ID.vertices.b = { ...BASE_CASE.vertices.b, ...{ x: 4, y: 3, id: 'payaso' } };

    const CASE_REGULAR = cloneDeep(BASE_CASE);
    CASE_REGULAR.vertices.a = { ...CASE_REGULAR.vertices.a, ...{ id: 'surprise' } };
    CASE_REGULAR.vertices.b = { ...CASE_REGULAR.vertices.b, ...{ id: 'mfker' } };

    it.each([
      ['Removes lines with 0 length', CASE_0, {}, {}],
      ['Removes lines with almost 0 length', CASE_ALMOST_0, {}, {}],
      ['Removes lines if vertices have the same id', CASE_SAME_ID, {}, {}],
      ['Do not remove lines that have more than 0 length', CASE_REGULAR, CASE_REGULAR.lines, CASE_REGULAR.vertices],
    ])('%s', (description, inputLayer, expectedLines, expectedVertices) => {
      const STATE = cloneDeep(MOCK_STATE);
      STATE.scene.layers[LAYER_ID] = inputLayer;

      const newState = Layer.removeZeroLengthLines(cloneDeep(STATE), LAYER_ID).updatedState;
      const { lines, vertices } = newState.scene.layers[LAYER_ID];
      expect(lines).toStrictEqual(expectedLines);
      expect(vertices).toStrictEqual(expectedVertices);
    });
  });

  describe('detectAndUpdateAreas', () => {
    const {
      CASE_LINES_INTERSECT,
      CASE_NOT_INTERSECT,
      CASE_LINES_INTERSECT_SPLITTED,
      CASE_SEPARATED_SHAPES,
      CASE_LINES_INTERSECT_WITH_A_LINE_NOT_CONNECTED_INSIDE,
      CASE_LINES_INTERSECT_WITH_LINES_INTERSECTING_INSIDE,
      CASE_WITH_A_SCALE_AREA,
    } = testCases;
    const lineProperties = {
      referenceLine: 'CENTER',
      height: { value: 220 },
      width: { value: 1 },
    };

    it.each([
      ['Creates an area from closed lines that intersects', CASE_LINES_INTERSECT],
      ['Do not create area with lines that do not intersect', CASE_NOT_INTERSECT],
      ['Creates areas from closed lines that are splitted', CASE_LINES_INTERSECT_SPLITTED],
      ['Creates areas from two sets of closed lines that are separated', CASE_SEPARATED_SHAPES],
      [
        'Creates an area from closed lines with a not connected line inside',
        CASE_LINES_INTERSECT_WITH_A_LINE_NOT_CONNECTED_INSIDE,
      ],
      [
        'Creates two areas from closed lines that are inside of another set of closed lines',
        CASE_LINES_INTERSECT_WITH_LINES_INTERSECTING_INSIDE,
      ],
    ])('%s', (description, testCase: AreaTestCase) => {
      const { input: inputLines, expectedOutput } = testCase;
      let state = getMockState(MOCK_STATE);

      state.scene.layers[LAYER_ID].lines = {};
      state.scene.layers[LAYER_ID].vertices = {};

      inputLines.forEach(line => {
        state = addLineToState(state, SeparatorsType.WALL, line, lineProperties, {
          createAuxVertices: true,
          forceVertexCreation: true,
        }).updatedState;
      });
      const updatedState = Layer.detectAndUpdateAreas(state, LAYER_ID).updatedState;

      const newState = updatedState;
      const newAreas: any = Object.values(newState.scene.layers[LAYER_ID].areas);
      expect(newAreas.length).toBe(expectedOutput.nrOfAreas);

      newAreas.forEach((area, areaIndex) => {
        area.coords.forEach((coords, index) => {
          expect(coords).toStrictEqual(expectedOutput.coordsByArea[areaIndex][index]);
        });
      });
    });

    it('Detects only scaled areas with `detectScaleAreasOnly`', () => {
      // Add regular lines to the test case so we ensure we only detect the scale-tool ones later
      const regularLines = CASE_SEPARATED_SHAPES.input;
      CASE_WITH_A_SCALE_AREA.input.lines = [...CASE_WITH_A_SCALE_AREA.input, ...regularLines];
      const { input: inputLines, expectedOutput } = CASE_WITH_A_SCALE_AREA;

      let state = getMockState(MOCK_STATE);
      state.scene.layers[LAYER_ID].lines = {};
      state.scene.layers[LAYER_ID].vertices = {};

      inputLines.forEach(line => {
        state = addLineToState(state, SeparatorsType.SCALE_TOOL, line, lineProperties, {
          createAuxVertices: true,
          forceVertexCreation: true,
        }).updatedState;
      });

      const updatedState = Layer.detectAndUpdateAreas(state, LAYER_ID, { detectScaleAreasOnly: true }).updatedState;

      const newState = updatedState;
      const newAreas: any = Object.values(newState.scene.layers[LAYER_ID].areas);

      expect(newAreas.length).toBe(expectedOutput.nrOfAreas);
      expect(newAreas.every(area => area.isScaleArea)).toBeTruthy();
    });
  });

  describe('Avoids creation of areas where enclosing lines are separated by tiny gap', () => {
    const constructLinesFromVertices = (state: any, vertices: Array<any>) => {
      const lineProperties = {
        width: { value: 5 },
        referenceLine: REFERENCE_LINE_POSITION.CENTER,
      };
      for (let i = 0; i < vertices.length - 1; i++) {
        const { x: x0, y: y0 } = vertices[i];
        const { x: x1, y: y1 } = vertices[i + 1];
        state = addLineToState(state, SeparatorsType.WALL, { x0, y0, x1, y1 }, lineProperties).updatedState;
      }
      return state;
    };

    let state;
    let linesFormingClosedSquare;

    beforeEach(() => {
      state = getCleanMockState();
      linesFormingClosedSquare = testCases.SQUARE_AREA_VERTICES;
    });

    it('Creates a single area within enclosed four lines of same length', () => {
      const vertices = linesFormingClosedSquare;
      state = constructLinesFromVertices(state, vertices);

      const updatedState = Layer.detectAndUpdateAreas(state, LAYER_ID).updatedState;
      const detectedAreas = updatedState.scene.layers[LAYER_ID].areas;
      const allDetectedAreas = Object.values(detectedAreas);
      expect(allDetectedAreas.length).toBe(1);
    });

    it.each([[0.1, 0.01, 0.001, 1e-9]]),
      "L-shaped wall segment inscribed into four closed lines with a tiny gap doesn't create a new area.",
      gapSize => {
        const vertices = [...linesFormingClosedSquare, { x: 0, y: 50 }, { x: 50, y: 50 }, { x: 50, y: gapSize }];
        state = constructLinesFromVertices(state, vertices);

        const updatedState = Layer.detectAndUpdateAreas(state, LAYER_ID).updatedState;
        const detectedAreas = updatedState.scene.layers[LAYER_ID].areas;
        const allDetectedAreas = Object.values(detectedAreas);
        expect(allDetectedAreas.length).toBe(1);
      };

    it.each([[0.1, 0.01, 0.001, 1e-9]]),
      "𐠒-shaped wall segments inscribed into four closed lines with a tiny gap don't create subareas.",
      gapSize => {
        const vertices = [
          ...linesFormingClosedSquare,
          { x: 50, y: 100 - gapSize },
          { x: 50, y: 0 + gapSize },
          { x: 0 + gapSize, y: 50 },
          { x: 100 - gapSize, y: 50 },
        ];
        state = constructLinesFromVertices(state, vertices);

        const updatedState = Layer.detectAndUpdateAreas(state, LAYER_ID).updatedState;
        const detectedAreas = updatedState.scene.layers[LAYER_ID].areas;
        const allDetectedAreas = Object.values(detectedAreas);
        expect(allDetectedAreas.length).toBe(1);
      };
  });

  describe('select & unselect', () => {
    let state;

    beforeEach(() => {
      state = getMockState({
        ...MOCK_STATE,
        scene: MOCK_SCENE,
      });
    });

    it.each([
      ['vertex', 'vertices'],
      ['line', 'lines'],
      ['hole', 'holes'],
      ['item', 'items'],
      ['area', 'areas'],
    ])('Properly selects and unselects %s element', (_, elementPrototype) => {
      const layer = state.scene.layers[LAYER_ID];
      const allElements = Object.values(layer[elementPrototype]) as any;
      const element = allElements[0];
      const selectedList = layer.selected[elementPrototype];

      expect(element.selected).toBeFalsy();
      expect(selectedList?.includes(element.id)).toBeFalsy();

      state = Layer.selectElement(state, LAYER_ID, elementPrototype, element.id).updatedState;

      let newLayer = state.scene.layers[LAYER_ID];
      let newElement = newLayer[elementPrototype][element.id];
      let newSelectedList = newLayer.selected[elementPrototype];

      expect(newElement.selected).toBeTruthy();
      expect(newSelectedList.includes(element.id)).toBeTruthy();

      state = Layer.unselect(state, LAYER_ID, elementPrototype, element.id).updatedState;

      newLayer = state.scene.layers[LAYER_ID];
      newElement = newLayer[elementPrototype][element.id];
      newSelectedList = newLayer.selected[elementPrototype];

      expect(newElement.selected).toBeFalsy();
      expect(newSelectedList.includes(element.id)).toBeFalsy();
    });

    it.each([['vertices'], ['lines'], ['holes'], ['items'], ['areas']])(
      'Select does not add duplicate IDs into the "selected" array of %s IDs',
      elementPrototype => {
        const layer = state.scene.layers[LAYER_ID];
        const allElements = Object.values(layer[elementPrototype]) as any;
        const element = allElements[0];
        const selectedList = layer.selected[elementPrototype];

        expect(element.selected).toBeFalsy();
        expect(selectedList?.includes(element.id)).toBeFalsy();

        for (let i = 0; i < 3; ++i) {
          state = Layer.selectElement(state, LAYER_ID, elementPrototype, element.id).updatedState;
        }

        const newLayer = state.scene.layers[LAYER_ID];
        const newElement = newLayer[elementPrototype][element.id];
        const newSelectedList = newLayer.selected[elementPrototype];

        expect(newElement.selected).toBeTruthy();
        expect(newSelectedList.filter(ID => ID === element.id).length).toEqual(1);
      }
    );
  });
  describe('unselectAll', () => {
    const assertElementSelectStatus = (
      state,
      elementID,
      prototype: typeof PrototypesEnum[keyof typeof PrototypesEnum],
      expectedSelectedStatus
    ) => {
      expect(state.scene.layers[LAYER_ID][prototype][elementID].selected).toEqual(expectedSelectedStatus);
      expect(state.scene.layers[LAYER_ID].selected[prototype].includes(elementID)).toEqual(expectedSelectedStatus);
    };

    it('Unselects all elements registered as selected in the layer', () => {
      let state = getMockState({ ...MOCK_STATE, scene: MOCK_SCENE });

      // Select every type of element (vertices are selected along lines)
      const [firstLineID] = Object.keys(state.scene.layers[LAYER_ID].lines);
      const [firstHoleId] = Object.keys(state.scene.layers[LAYER_ID].holes);
      const [firstItemId] = Object.keys(state.scene.layers[LAYER_ID].items);
      const [firstAreaId] = Object.keys(state.scene.layers[LAYER_ID].areas);
      state = Line.select(cloneDeep(state), LAYER_ID, firstLineID, { unselectAllBefore: false }).updatedState;
      state = Hole.select(cloneDeep(state), LAYER_ID, firstHoleId, { unselectAllBefore: false }).updatedState;
      state = Item.select(cloneDeep(state), LAYER_ID, firstItemId, { unselectAllBefore: false }).updatedState;
      state = Area.select(cloneDeep(state), LAYER_ID, firstAreaId, { unselectAllBefore: false }).updatedState;

      // Ensure they are selected
      assertElementSelectStatus(state, firstLineID, 'lines', true);
      assertElementSelectStatus(state, firstHoleId, 'holes', true);
      assertElementSelectStatus(state, firstItemId, 'items', true);
      assertElementSelectStatus(state, firstAreaId, 'areas', true);
      state.scene.layers[LAYER_ID].lines[firstLineID].vertices.forEach(vertexID => {
        assertElementSelectStatus(state, vertexID, 'vertices', true);
      });

      const newState = Layer.unselectAll(cloneDeep(state), LAYER_ID).updatedState;

      // Ensure everything is deselected
      assertElementSelectStatus(newState, firstLineID, 'lines', false);
      assertElementSelectStatus(newState, firstHoleId, 'holes', false);
      assertElementSelectStatus(newState, firstItemId, 'items', false);
      assertElementSelectStatus(newState, firstAreaId, 'areas', false);
      newState.scene.layers[LAYER_ID].lines[firstLineID].vertices.forEach(vertexID => {
        assertElementSelectStatus(newState, vertexID, 'vertices', false);
      });
    });
  });
});
