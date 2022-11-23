import { Position } from 'geojson';
import { ProviderStorage } from 'archilyse-ui-components';
import { Hole, Item, Line, Selection, Vertex } from '../types';
import { MOCK_COPY_PASTE_STORAGE } from '../tests/utils';
import { SeparatorsType } from '../constants';
import { detectItemsUnderSelection, detectLinesUnderSelection } from '../utils/copy-paste-utils';
import { addLineToState, getMockState } from '../tests/utils/tests-utils';
import { CopyPaste, Hole as HoleClass, Item as ItemClass, Line as LineClass, Vertex as VertexClass } from './export';
import { MOCK_STATE_WITH_TWO_LINES, SELECTED_LAYER_ID } from './copyPaste.testMocks';

let state;

const assertNewCoordinates = (updatedElements: (Line | Hole)[], expectedCoords: Position[][][]) => {
  const updatedElementCoordinates = updatedElements.map(element => element.coordinates);
  updatedElementCoordinates.forEach((elementCoordinates: Position[][], elementIndex) => {
    elementCoordinates.forEach((coordinate: Position[], index) => {
      expect(coordinate).toStrictEqual(expectedCoords[elementIndex][index]);
    });
  });
};
const assertNewPosition = (updatedElements: (Vertex | Item)[], expectedCoords: Position[]) => {
  updatedElements.forEach((element, index) => {
    expect(element.x).toBe(expectedCoords[index][0]);
    expect(element.y).toBe(expectedCoords[index][1]);
  });
};

const assertElementsSelected = (elementsToSelect, elementPrototype: 'lines' | 'items' | 'holes', ElementClass) => {
  const { updatedState } = CopyPaste.selectElements(state, SELECTED_LAYER_ID, elementsToSelect, ElementClass);

  const elements = updatedState.scene.layers[SELECTED_LAYER_ID][elementPrototype];
  elementsToSelect.forEach(element => {
    const updatedElement = elements[element.id];
    expect(updatedElement.selected).toBe(true);
  });

  const elementsToSelectIDs = elementsToSelect.map(element => element.id);
  const selectedLayerElements = updatedState.scene.layers[SELECTED_LAYER_ID].selected[elementPrototype];
  expect(selectedLayerElements).toStrictEqual(elementsToSelectIDs);
};

const assertElementsCloned = (originalElements, elementsToClone, notClonedFields, ElementClass) => {
  const { clonedElements } = CopyPaste.cloneElements(state, SELECTED_LAYER_ID, elementsToClone, ElementClass);
  clonedElements.forEach((clonedElement, index) => {
    const element = clonedElement;
    const expectedElement: any = originalElements[index];

    Object.keys(element)
      .filter(key => !notClonedFields.includes(key))
      .forEach(key => {
        expect(element[key]).toStrictEqual(expectedElement[key]);
      });

    notClonedFields.forEach(field => {
      expect(element[field]).not.toBe(expectedElement[field]);
    });
  });
};

describe('detectLinesUnderSelection', () => {
  beforeEach(() => {
    state = getMockState(MOCK_STATE_WITH_TWO_LINES);
  });

  it('With a selection not covering any lines, it should not detect any line', () => {
    const startPosition = { x: 0, y: 0 };
    const endPosition = { x: 0, y: 0 };

    const detectedLines = detectLinesUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedLines.length).toBe(0);
  });

  it('With a selection covering totally a line, it should detect a line', () => {
    const startPosition = { x: 314, y: 1148 };
    const endPosition = { x: 583, y: 1091 };

    const [_, EXPECTED_LINE] = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines);

    const detectedLines = detectLinesUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedLines.length).toBe(1);

    const [detectedLine] = detectedLines;
    expect(detectedLine).toEqual(EXPECTED_LINE);
  });

  it('With two lines partially covered by the selection, it should detect two lines', () => {
    const startPosition = { x: 304, y: 1157 };
    const endPosition = { x: 466, y: 1013 };

    const EXPECTED_LINES = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines);

    const detectedLines = detectLinesUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedLines.length).toBe(2);

    detectedLines.forEach((detectedLine, index) => {
      expect(detectedLine).toEqual(EXPECTED_LINES[index]);
    });
  });
});

describe('detectItemsUnderSelection', () => {
  beforeEach(() => {
    state = getMockState(MOCK_STATE_WITH_TWO_LINES);
  });

  it('With a selection not covering any items, it should not detect any item', () => {
    const startPosition = { x: 0, y: 0 };
    const endPosition = { x: 0, y: 0 };

    const detectedItems = detectItemsUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedItems.length).toBe(0);
  });

  it('With a selection covering totally a item, it should detect an item', () => {
    const startPosition = { x: 380, y: 900 };
    const endPosition = { x: 399, y: 970 };

    const [_, EXPECTED_ITEM] = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items);

    const detectedItems = detectItemsUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedItems.length).toBe(1);

    const [detectedItem] = detectedItems;
    expect(detectedItem).toEqual(EXPECTED_ITEM);
  });

  it('With two items partially covered by the selection, it should detect two items', () => {
    const startPosition = { x: 340, y: 900 };
    const endPosition = { x: 399, y: 970 };

    const EXPECTED_ITEMS = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items);

    const detectedItems = detectItemsUnderSelection(state, SELECTED_LAYER_ID, startPosition, endPosition);
    expect(detectedItems.length).toEqual(2);

    detectedItems.forEach((detectedItem, index) => {
      expect(detectedItem).toEqual(EXPECTED_ITEMS[index]);
    });
  });
});

describe('CopyPaste class methods', () => {
  beforeEach(() => {
    state = getMockState(MOCK_STATE_WITH_TWO_LINES);
  });

  describe('cloneElements', () => {
    it('Create identical lines as the passed ones with a different line id, vertices & aux vertices', () => {
      const NOT_CLONED_FIELDS = ['id', 'vertices', 'auxVertices', 'holes'];
      const originalLines = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines);
      const linesToClone = originalLines.map(line => line);
      assertElementsCloned(originalLines, linesToClone, NOT_CLONED_FIELDS, LineClass);
    });
    it('Create identical items as the passed ones with a different item id', () => {
      const NOT_CLONED_FIELDS = ['id'];
      const originalItems = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items);
      const itemsToClone = originalItems.map(item => item);
      assertElementsCloned(originalItems, itemsToClone, NOT_CLONED_FIELDS, ItemClass);
    });
    it('Create identical vertices as the passed ones with a different item id', () => {
      const NOT_CLONED_FIELDS = ['id'];
      const originalVertices = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].vertices);
      const verticesToClone = originalVertices.map(item => item);
      assertElementsCloned(originalVertices, verticesToClone, NOT_CLONED_FIELDS, VertexClass);
    });
    it('Create identical holes as the passed ones with a different item id', () => {
      const NOT_CLONED_FIELDS = ['id'];
      const originalHoles = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes);
      const holesToClone = originalHoles.map(hole => hole);
      assertElementsCloned(originalHoles, holesToClone, NOT_CLONED_FIELDS, HoleClass);
    });
  });

  describe('selectElements', () => {
    it('Marks passed lines as "selected" in the state', () => {
      const STATE_LINES = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines);
      const linesToSelect = STATE_LINES.map(line => line);
      assertElementsSelected(linesToSelect, 'lines', LineClass);
    });
    it('Marks passed items as "selected" in the state', () => {
      const STATE_ITEMS = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items);
      const itemsToSelect = STATE_ITEMS.map(item => item);
      assertElementsSelected(itemsToSelect, 'items', ItemClass);
    });
    it('Marks passed holes as "selected" in the state', () => {
      const STATE_HOLES = Object.values(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes);
      const holesToSelect = STATE_HOLES.map(hole => hole);
      assertElementsSelected(holesToSelect, 'holes', HoleClass);
    });
  });

  describe('deleteCurrentSelection', () => {
    it('Delete lines, items and holes in current selection and initialize it', () => {
      const MOCK_SELECTION: Selection = {
        draggingPosition: { x: 2015, y: 13433 },
        startPosition: { x: 304, y: 1157 },
        endPosition: { x: 466, y: 1013 },
        lines: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines),
        items: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items),
        holes: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes),
      };
      state = {
        ...state,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };

      const { updatedState } = CopyPaste.deleteCurrentSelection(state);

      // Lines are erased from the state
      const updatedLines = updatedState.scene.layers[SELECTED_LAYER_ID].lines;
      MOCK_SELECTION.lines.forEach(lineID => {
        expect(updatedLines[lineID]).toBe(undefined);
      });

      // Items are erased from the state
      const updatedItems = updatedState.scene.layers[SELECTED_LAYER_ID].lines;
      MOCK_SELECTION.items.forEach(itemID => {
        expect(updatedItems[itemID]).toBe(undefined);
      });

      // Holes are erased from the state
      const updatedHoles = updatedState.scene.layers[SELECTED_LAYER_ID].holes;
      MOCK_SELECTION.holes.forEach(itemID => {
        expect(updatedHoles[itemID]).toBe(undefined);
      });

      // Selection is initialized
      const { selection: expectedSelection } = updatedState.copyPaste;
      expect(expectedSelection.startPosition).toStrictEqual({ x: -1, y: -1 });
      expect(expectedSelection.endPosition).toStrictEqual({ x: -1, y: -1 });
      expect(expectedSelection.draggingPosition).toStrictEqual({ x: -1, y: -1 });
      expect(expectedSelection.lines).toStrictEqual([]);
      expect(expectedSelection.items).toStrictEqual([]);
      expect(expectedSelection.holes).toStrictEqual([]);

      expect(updatedState.copyPaste.drawing).toBe(false);
      expect(updatedState.copyPaste.dragging).toBe(false);
      expect(updatedState.copyPaste.rotating).toBe(false);
    });
  });

  describe('upgradeDraggingPosition', () => {
    it('Calculates the new position of the rectangle so the cursor is always at the center of it', () => {
      const EXPECTED_DRAGGING_POSITION = {
        x: 419,
        y: 828,
      };

      const MOCK_CURSOR_POSITION = { x: 500, y: 900 };

      const MOCK_SELECTION = {
        startPosition: { x: 304, y: 1157 },
        endPosition: { x: 466, y: 1013 },
        draggingPosition: { x: -1, y: -1 },
        lines: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines),
      };
      state = {
        ...state,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };

      const { updatedState } = CopyPaste.updateDraggingPosition(state, MOCK_CURSOR_POSITION.x, MOCK_CURSOR_POSITION.y);

      const { draggingPosition } = updatedState.copyPaste.selection;
      expect(draggingPosition.x).toBe(EXPECTED_DRAGGING_POSITION.x);
      expect(draggingPosition.y).toBe(EXPECTED_DRAGGING_POSITION.y);
    });
  });

  describe('translateCopyPasteSelection', () => {
    beforeEach(() => {
      CopyPaste.previousSelectionCenter = { x: 400, y: 800 }; // Mock previous location
    });
    afterAll(() => {
      CopyPaste.previousSelectionCenter = { x: undefined, y: undefined };
    });

    const EXPECTED_NEW_LINE_COORDINATES = [
      [
        [
          [460.307693970492, 1139.07911863776],
          [646.180752250087, 1139.07911863776],
          [646.180752250087, 1159.07911863776],
          [460.307693970492, 1159.07911863776],
          [460.307693970492, 1139.07911863776],
        ],
      ],
      [
        [
          [464.279340514928, 1208.185768510943],
          [646.180752250087, 1208.185768510943],
          [646.180752250087, 1228.185768510943],
          [464.279340514928, 1228.185768510943],
          [464.279340514928, 1208.185768510943],
        ],
      ],
    ];

    const EXPECTED_NEW_ITEM_COORDS = [
      [450, 1100],
      [490, 1050],
    ];

    const EXPECTED_NEW_HOLE_COORDS = [
      [
        [
          [460.51494277881403, 1123.2912736246635],
          [460.51494277881403, 1141.188560375337],
          [460.51494277881403, 1141.188560375337],
          [532.104089781508, 1123.2912736246635],
          [532.104089781508, 1141.188560375337],
        ],
      ],
    ];

    const EXPECTED_NEW_HOLE_SWEEPING_POINTS = [
      {
        angle_point: [536.309516280161, 1132.2399170000003],
        closed_point: [456.309516280161, 1132.2399170000003],
        opened_point: [536.309516280161, 1212.2399170000003],
      },
    ];

    it('Translate every vertex of the copied lines, the items & holes using the new position ', () => {
      const MOCK_VERTICES_IDS = Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].vertices);
      const MOCK_SELECTION = {
        startPosition: { x: 304, y: 1157 },
        endPosition: { x: 466, y: 1013 },
        draggingPosition: { x: 419, y: 828 },
        rotation: 0,
        lines: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines),
        items: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items),
        holes: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes),
      };
      state = {
        ...state,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };

      // Mock the selected elements in the state
      state = {
        ...state,
        scene: {
          ...state.scene,
          layers: {
            ...state.scene.layers,
            [SELECTED_LAYER_ID]: {
              ...state.scene.layers[SELECTED_LAYER_ID],
              selected: {
                ...state.scene.layers[SELECTED_LAYER_ID].selected,
                lines: MOCK_SELECTION.lines,
                items: MOCK_SELECTION.items,
                holes: MOCK_SELECTION.holes,
                vertices: MOCK_VERTICES_IDS,
              },
            },
          },
        },
      };

      const { updatedState } = CopyPaste.translateCopyPasteSelectionFromDocument(state);

      const updatedItems: Item[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].items);
      const updatedLines: Line[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].lines);
      const updatedHoles: Hole[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].holes);

      assertNewPosition(updatedItems, EXPECTED_NEW_ITEM_COORDS);
      assertNewCoordinates(updatedLines, EXPECTED_NEW_LINE_COORDINATES);
      assertNewCoordinates(updatedHoles, EXPECTED_NEW_HOLE_COORDS);

      updatedHoles.forEach((hole, index) => {
        if (!hole.door_sweeping_points) return;
        const expectedSweepingPoints = EXPECTED_NEW_HOLE_SWEEPING_POINTS[index];
        expect(hole.door_sweeping_points.angle_point).toStrictEqual(expectedSweepingPoints.angle_point);
        expect(hole.door_sweeping_points.closed_point).toStrictEqual(expectedSweepingPoints.closed_point);
        expect(hole.door_sweeping_points.opened_point).toStrictEqual(expectedSweepingPoints.opened_point);
      });
    });

    describe('rotateCopyPasteSelection', () => {
      const EXPECTED_NEW_LINE_COORDINATES = [
        [
          [
            [360.9208813622399, 760.307693970492],
            [360.9208813622399, 946.180752250087],
            [340.9208813622399, 946.180752250087],
            [340.9208813622399, 760.307693970492],
            [360.9208813622399, 760.307693970492],
          ],
        ],
        [
          [
            [291.81423148905697, 764.279340514928],
            [291.81423148905697, 946.180752250087],
            [271.81423148905697, 946.180752250087],
            [271.81423148905697, 764.279340514928],
            [291.81423148905697, 764.279340514928],
          ],
        ],
      ];

      const EXPECTED_NEW_ITEM_COORDS = [
        [400, 750],
        [450, 790],
      ];

      const EXPECTED_NEW_HOLE_COORDS = [
        [
          [
            [376.7087263753366, 760.514942778814],
            [358.8114396246631, 760.514942778814],
            [358.8114396246631, 760.514942778814],
            [376.7087263753366, 832.104089781508],
            [358.8114396246631, 832.104089781508],
          ],
        ],
      ];

      const EXPECTED_NEW_HOLE_SWEEPING_POINTS = [
        {
          angle_point: [367.7600829999998, 836.309516280161],
          closed_point: [367.7600829999998, 756.309516280161],
          opened_point: [287.7600829999998, 836.309516280161],
        },
      ];

      it('Rotate every vertex of the copied lines & items using the new rotation', () => {
        const MOCK_VERTICES_IDS = Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].vertices);
        const MOCK_SELECTION = {
          startPosition: { x: 304, y: 1157 },
          endPosition: { x: 466, y: 1013 },
          draggingPosition: { x: 419, y: 828 },
          rotation: 90,
          lines: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].lines),
          items: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].items),
          holes: Object.keys(MOCK_STATE_WITH_TWO_LINES.scene.layers[SELECTED_LAYER_ID].holes),
        };
        // Mock the selected elements in the state
        state = {
          ...state,
          copyPaste: {
            ...state.copyPaste,
            selection: MOCK_SELECTION,
          },
          scene: {
            ...state.scene,
            layers: {
              ...state.scene.layers,
              [SELECTED_LAYER_ID]: {
                ...state.scene.layers[SELECTED_LAYER_ID],
                selected: {
                  ...state.scene.layers[SELECTED_LAYER_ID].selected,
                  lines: MOCK_SELECTION.lines,
                  items: MOCK_SELECTION.items,
                  holes: MOCK_SELECTION.holes,
                  vertices: MOCK_VERTICES_IDS,
                },
              },
            },
          },
        };

        const { updatedState } = CopyPaste.rotateCopyPasteSelectionFromDocument(state);

        const updatedItems: Item[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].items);
        const updatedLines: Line[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].lines);
        const updatedHoles: Hole[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].holes);

        assertNewPosition(updatedItems, EXPECTED_NEW_ITEM_COORDS);
        updatedItems.forEach(item => {
          expect(item.rotation).toBe(MOCK_SELECTION.rotation);
        });
        assertNewCoordinates(updatedLines, EXPECTED_NEW_LINE_COORDINATES);
        assertNewCoordinates(updatedHoles, EXPECTED_NEW_HOLE_COORDS);

        updatedHoles.forEach((hole, index) => {
          if (!hole.door_sweeping_points) return;
          const expectedSweepingPoints = EXPECTED_NEW_HOLE_SWEEPING_POINTS[index];
          expect(hole.door_sweeping_points.angle_point).toStrictEqual(expectedSweepingPoints.angle_point);
          expect(hole.door_sweeping_points.closed_point).toStrictEqual(expectedSweepingPoints.closed_point);
          expect(hole.door_sweeping_points.opened_point).toStrictEqual(expectedSweepingPoints.opened_point);
        });
      });
    });
  });

  describe('restoreCopyPasteSelection', () => {
    beforeEach(() => {
      state = getMockState({ scaleValidated: true });
    });

    it('Restores a copy paste selection in the local storage, recreating its elements in the state', () => {
      jest.spyOn(ProviderStorage, 'get').mockImplementation(() => JSON.stringify(MOCK_COPY_PASTE_STORAGE));
      const updatedState = CopyPaste.restoreCopyPasteFromAnotherPlan(state).updatedState;
      const newLines: Line[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].lines);
      const newItems: Item[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].items);
      const newVertices: Vertex[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].vertices);
      const newHoles: Hole[] = Object.values(updatedState.scene.layers[SELECTED_LAYER_ID].holes);

      // There should be the same number of lines, items & total vertices - 4 shared (with a default scale of 1, samePoints() detects 4 vertices)
      expect(newLines.length).toBe(MOCK_COPY_PASTE_STORAGE.elements.lines.length);
      expect(newItems.length).toBe(MOCK_COPY_PASTE_STORAGE.elements.items.length);
      expect(newVertices.length).toBe(MOCK_COPY_PASTE_STORAGE.elements.vertices.length - 4);
      expect(newHoles.length).toBe(MOCK_COPY_PASTE_STORAGE.elements.holes.length);

      // And the elements have the same position/coords as before
      MOCK_COPY_PASTE_STORAGE.elements.vertices.forEach(originalVertex => {
        const vertexInSamePlace = newVertices.find(
          newVertex => newVertex.x === originalVertex.x && newVertex.y === originalVertex.y
        );
        expect(vertexInSamePlace);
      });

      MOCK_COPY_PASTE_STORAGE.elements.items.forEach(originalItem => {
        const itemInSamePlace = newItems.find(newItem => newItem.x === originalItem.x && newItem.y === originalItem.y);
        expect(itemInSamePlace);
      });

      MOCK_COPY_PASTE_STORAGE.elements.holes.forEach(originalItem => {
        const holesInTheSamePlace = newHoles.find(
          newHole => JSON.stringify(newHole.coordinates) === JSON.stringify(originalItem.coordinates)
        );
        expect(holesInTheSamePlace);
      });
    });
  });

  describe('mergeEqualVertices', () => {
    const MOCK_LINE_PROPERTIES = {
      height: {
        unit: 'cm',
        value: 300,
      },
      referenceLine: 'OUTSIDE_FACE',
      width: {
        unit: 'cm',
        value: 20,
      },
    };
    const MOCK_SELECTION = {
      startPosition: { x: 0, y: 0 },
      endPosition: { x: 500, y: 500 },
      draggingPosition: { x: -1, y: -1 },
      rotation: 0,
      lines: [],
    };

    const createSelectedLines = (state, line1Points, line2Points, type1, type2) => {
      const createLine1Result = addLineToState(
        state,
        type1,
        {
          x0: line1Points.x1,
          y0: line1Points.y1,
          x1: line1Points.x2,
          y1: line1Points.y2,
        },
        MOCK_LINE_PROPERTIES
      );

      state = createLine1Result.updatedState;
      const createLine2Result = addLineToState(
        state,
        type2,
        {
          x0: line2Points.x1,
          y0: line2Points.y1,
          x1: line2Points.x2,
          y1: line2Points.y2,
        },
        MOCK_LINE_PROPERTIES
      );
      state = createLine2Result.updatedState;
      state = {
        ...state,
        copyPaste: {
          ...state.copyPaste,
          selection: MOCK_SELECTION,
        },
      };
      const selectedLines = [createLine1Result.line, createLine2Result.line];
      state = CopyPaste.cloneAndSelectElements(state, SELECTED_LAYER_ID, selectedLines, []).updatedState;
      return { updatedState: state };
    };
    beforeEach(() => {
      state = getMockState({ scaleValidated: true });
      state = {
        ...state,
        scene: {
          ...state.scene,
          scale: 1,
        },
      };
    });

    it('Merge equal vertices of a copy paste selection', () => {
      // With these points the lines will share 3 vertices (1 main + 2 aux)
      const linePoints1 = { x1: 10, y1: 10, x2: 200, y2: 10 };
      const linePoints2 = { x1: 200, y1: 10, x2: 400, y2: 10 };
      state = createSelectedLines(state, linePoints1, linePoints2, SeparatorsType.WALL, SeparatorsType.WALL)
        .updatedState;

      //  6 vertices per line * 4  - 3 shared vertices (from original lines) = 21
      let allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(21);

      state = CopyPaste.mergeEqualVertices(state).updatedState;

      // 6 shared vertices =  24 vertices (6 * 4 lines) - 6  = 18
      allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(18);
    });

    it('If there are no equal vertices, do nothing', () => {
      // No shared points
      const linePoints1 = { x1: 10, y1: 10, x2: 200, y2: 10 };
      const linePoints2 = { x1: 250, y1: 10, x2: 400, y2: 10 };
      state = createSelectedLines(state, linePoints1, linePoints2, SeparatorsType.WALL, SeparatorsType.WALL)
        .updatedState;

      // No shared vertices initially: 6 vertices * 4 lines = 24
      let allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);

      state = CopyPaste.mergeEqualVertices(state).updatedState;

      // No shared vertices: 6 vertices * 4 lines = 12
      allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);
    });

    it('Does not merge vertices with two area splitters', () => {
      // Shared points
      const linePoints1 = { x1: 10, y1: 10, x2: 200, y2: 10 };
      const linePoints2 = { x1: 200, y1: 10, x2: 400, y2: 10 };
      state = createSelectedLines(
        state,
        linePoints1,
        linePoints2,
        SeparatorsType.AREA_SPLITTER,
        SeparatorsType.AREA_SPLITTER
      ).updatedState;

      // No shared vertices initially: 6 vertices * 4 lines = 24
      let allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);

      state = CopyPaste.mergeEqualVertices(state).updatedState;

      // No shared vertices created: 6 vertices * 4 lines = 24
      allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);
    });

    it('Does not merge vertices with one area splitter and a line connected by one vertex', () => {
      // Shared points
      const linePoints1 = { x1: 10, y1: 10, x2: 200, y2: 10 };
      const linePoints2 = { x1: 200, y1: 10, x2: 400, y2: 10 };
      state = createSelectedLines(state, linePoints1, linePoints2, SeparatorsType.WALL, SeparatorsType.AREA_SPLITTER)
        .updatedState;

      // No shared vertices initially: 6 vertices * 4 lines = 24
      let allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);

      state = CopyPaste.mergeEqualVertices(state).updatedState;

      // No shared vertices created: 6 vertices * 4 lines = 24
      allVertices = Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices);
      expect(allVertices.length).toBe(24);
    });
  });
});
