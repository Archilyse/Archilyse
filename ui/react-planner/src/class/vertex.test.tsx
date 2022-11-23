import { cloneDeep, IDBroker } from '../utils/export';
import { MOCK_STATE } from '../tests/utils';
import { SeparatorsType, VERTEX_ROUNDING_PRECISION } from '../constants';
import { addLineToState, getCleanMockState, getMockState, SELECTED_LAYER_ID } from '../tests/utils/tests-utils';
import { Vertex as VertexType } from '../types';
import { Line, Vertex } from './export';

const LAYER_ID = MOCK_STATE.scene.selectedLayer;
const DEFAULT_SNAP_MASK = { SNAP_POINT: true, SNAP_SEGMENT: true };

const roundVertex = v => parseFloat(v.toFixed(VERTEX_ROUNDING_PRECISION));

describe('Vertex class methods', () => {
  const relatedPrototype = 'lines';
  const relatedID = IDBroker.acquireID(); // Same as in Line.crate
  const assertVertexIsAddedToState = (updatedState, expectedVertex) => {
    const expectedUpdatedState = updatedState;
    const newVertices = expectedUpdatedState.scene.layers[LAYER_ID].vertices;
    expect(newVertices[expectedVertex.id]).toBeTruthy();
  };

  const assertVertexIsRemovedFromState = (updatedState, expectedVertex) => {
    const expectedUpdatedState = updatedState;
    const newVertices = expectedUpdatedState.scene.layers[LAYER_ID].vertices;
    expect(newVertices[expectedVertex.id]).toBeFalsy();
  };

  describe('Add', () => {
    it('Add a new vertex', () => {
      const x = 1;
      const y = 1;
      const { updatedState, vertex } = Vertex.add(MOCK_STATE, LAYER_ID, x, y, relatedPrototype, relatedID);

      const expectedVertex = vertex;
      expect(expectedVertex.x).toBe(x);
      expect(expectedVertex.y).toBe(y);
      expect(expectedVertex.lines[0]).toBe(relatedID);

      assertVertexIsAddedToState(updatedState, expectedVertex);
    });

    it(`Adding a vertex to the same line twice, won't duplicate the lineID inside ${relatedPrototype} the array`, () => {
      const x = 1;
      const y = 1;
      const addResult = Vertex.add(MOCK_STATE, LAYER_ID, x, y, relatedPrototype, relatedID);
      let updatedState = addResult.updatedState;
      const vertex = addResult.vertex;

      updatedState = Vertex.add(updatedState, LAYER_ID, x, y, relatedPrototype, relatedID).updatedState;

      const updatedVertex = updatedState.scene.layers[LAYER_ID].vertices[vertex.id];
      const relatedIDs = updatedVertex[relatedPrototype].filter(ID => ID === relatedID);

      assertVertexIsAddedToState(updatedState, vertex);
      expect(relatedIDs.length).toEqual(1);
    });

    it(`Add a new vertex, rounding up its coordinates to its ${VERTEX_ROUNDING_PRECISION}th decimal`, () => {
      const x = 1123.1234567891012;
      const y = 112.1234567891012;
      const { updatedState, vertex } = Vertex.add(MOCK_STATE, LAYER_ID, x, y, relatedPrototype, relatedID);

      const expectedVertex = vertex;

      expect(expectedVertex.x).toBe(roundVertex(x));
      expect(expectedVertex.y).toBe(roundVertex(y));
      expect(expectedVertex.lines[0]).toBe(relatedID);

      assertVertexIsAddedToState(updatedState, expectedVertex);
    });

    it('"Merges" vertices if they share the same point', () => {
      let state = getCleanMockState();

      const linePoints = { x0: 10, y0: 10, x1: 20, y1: 20 };
      state = addLineToState(state, SeparatorsType.WALL, linePoints).updatedState;

      const initialVertices = state.scene.layers[SELECTED_LAYER_ID].vertices;
      const allInitialVertices = Object.values(initialVertices);
      expect(allInitialVertices.length).toBe(6);

      // Add a vertex in the same spot as another one with a mock line ID
      state = Vertex.add(state, SELECTED_LAYER_ID, linePoints.x1, linePoints.y1, relatedPrototype, relatedID)
        .updatedState;

      // Expect same nr of vertices because the new vertex is reused from the initial ones
      const newVertices = state.scene.layers[SELECTED_LAYER_ID].vertices;
      const allNewVertices = Object.values(newVertices);
      expect(allNewVertices.length).toBe(allInitialVertices.length);
    });

    it('Does not "merge" vertices if they share the same point and are in the same line', () => {
      let state = getCleanMockState();

      const linePoints = { x0: 10, y0: 10, x1: 20, y1: 20 };
      const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, linePoints);
      state = updatedState;

      const initialVertices = state.scene.layers[SELECTED_LAYER_ID].vertices;
      const allInitialVertices = Object.values(initialVertices);
      expect(allInitialVertices.length).toBe(6);

      // Add a vertex in the same spot as another one and in the same line (this happens while drawing/replacing aux vertices)
      state = Vertex.add(state, SELECTED_LAYER_ID, linePoints.x1, linePoints.y1, relatedPrototype, line.id)
        .updatedState;

      // The vertex will be added
      const newVertices = state.scene.layers[SELECTED_LAYER_ID].vertices;
      const allNewVertices = Object.values(newVertices);
      expect(allNewVertices.length).toBe(allInitialVertices.length + 1);
    });
  });

  describe('Remove', () => {
    let state;
    const x = 1;
    const y = 1;
    const mockVertexWithMultipleRelations = (state, n = 3) => {
      for (let i = 0; i < n; i++) {
        state = Vertex.add(state, LAYER_ID, x, y, relatedPrototype, IDBroker.acquireID()).updatedState;
      }
      return state;
    };

    beforeEach(() => {
      const STATE = cloneDeep(MOCK_STATE);
      STATE.scene.layers[LAYER_ID].vertices = {};
      state = STATE;
    });

    it('Removing a selected vertex is also removing its ID from the selected vertices list', () => {
      const addResult = Vertex.add(state, LAYER_ID, x, y, relatedPrototype, relatedID);
      let updatedState = addResult.updatedState;
      const vertex = addResult.vertex;

      updatedState = Vertex.select(updatedState, LAYER_ID, vertex.id).updatedState;

      assertVertexIsAddedToState(updatedState, vertex);

      expect(updatedState.scene.layers[LAYER_ID].vertices[vertex.id].selected).toBeTruthy();
      expect(updatedState.scene.layers[LAYER_ID].selected.vertices.includes(vertex.id)).toBeTruthy();

      updatedState = Vertex.remove(updatedState, LAYER_ID, vertex.id, relatedPrototype, relatedID).updatedState;

      assertVertexIsRemovedFromState(updatedState, vertex);
      expect(updatedState.scene.layers[LAYER_ID].vertices[vertex.id]).toBeFalsy();
      expect(updatedState.scene.layers[LAYER_ID].selected.vertices.includes(vertex.id)).toBeFalsy();
    });

    it('Removes a vertex without relatedPrototype, removing the vertex ignoring all its relations', () => {
      const n = 3;
      state = mockVertexWithMultipleRelations(state, n);

      const allVertices = Object.values(state.scene.layers[LAYER_ID].vertices) as any;
      const vertex = allVertices[0];
      expect(vertex[relatedPrototype].length).toStrictEqual(n);

      state = Vertex.remove(state, LAYER_ID, vertex.id).updatedState;

      assertVertexIsRemovedFromState(state, vertex);
    });

    it('Removes a vertex with relatedPrototype, removing its relations and the vertex if the related list is empty', () => {
      const n = 3;
      state = mockVertexWithMultipleRelations(state, n);

      const allVertices = Object.values(state.scene.layers[LAYER_ID].vertices) as any;
      const vertex = allVertices[0];
      expect(vertex[relatedPrototype].length).toStrictEqual(n);

      const vertexLineIds = vertex[relatedPrototype];

      for (let i = 0; i < vertexLineIds.length; i++) {
        const vertexLineId = vertexLineIds[i];
        state = Vertex.remove(state, LAYER_ID, vertex.id, relatedPrototype, vertexLineId).updatedState;

        // checks if vertex is removed completely after all lines were removed.
        const lastLoop = i === vertexLineIds.length - 1;
        if (lastLoop) {
          expect(state.scene.layers[LAYER_ID].vertices[vertex.id]).toBeFalsy();
        } else {
          const updatedVertex = state.scene.layers[LAYER_ID].vertices[vertex.id];
          const updatedRelatedIDs = updatedVertex[relatedPrototype];
          expect(updatedRelatedIDs.includes(vertexLineId)).toBeFalsy();
        }
      }
    });
  });

  describe('updateCoords', () => {
    let state;

    beforeEach(() => {
      state = getMockState();
    });

    it('Updates coords & round them', () => {
      const newX = 123.313;
      const newY = 1232.1;
      const allVertices = Object.values(state.scene.layers[LAYER_ID].vertices) as any;
      const vertexIDToUpdate = allVertices[0].id;
      const { updatedState } = Vertex.updateCoords(state, LAYER_ID, vertexIDToUpdate, newX, newY);

      // Vertex is updated & rounded
      const expectedVertex = updatedState.scene.layers[LAYER_ID].vertices[vertexIDToUpdate];
      expect(expectedVertex.x).toBe(roundVertex(newX));
      expect(expectedVertex.y).toBe(roundVertex(newY));
    });
    it('Orders related line main vertices if needed', () => {
      // Check vertex order in line
      const allLines = Object.values(state.scene.layers[LAYER_ID].lines) as any;
      const line = allLines[0];
      const lineVertices = line.vertices;
      expect(lineVertices).toStrictEqual(['a', 'b']);

      // Update the first vertex with a value that makes it bigger than the second vertex in line.vertices
      const newX = 4;
      const newY = 9;
      const [vertexIDToUpdate] = lineVertices;
      const { updatedState } = Vertex.updateCoords(state, LAYER_ID, vertexIDToUpdate, newX, newY);

      // The line.vertices relationship is re-ordered so the updated vertex is now in second place
      const allNewLines = Object.values(updatedState.scene.layers[LAYER_ID].lines) as any;
      const newLine = allNewLines[0];
      const newLineVertices = newLine.vertices;
      expect(newLineVertices).toStrictEqual(['b', 'a']);
    });
  });

  describe('updateDraggingVertex', () => {
    const INCR = 20;
    let state;
    let x;
    let y;
    let originalVertexID;
    let originalVertex;

    beforeEach(() => {
      // Setup a clean state with snaps enabled
      state = getCleanMockState();
      state.snapMask = DEFAULT_SNAP_MASK;

      // Create an horizontal line, like "-----"
      const linePoints = { x0: 10, y0: 10, x1: 20, y1: 10 };
      const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, linePoints);
      state = updatedState;

      originalVertexID = line.vertices[0];
      originalVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[originalVertexID];

      x = originalVertex.x;
      y = originalVertex.y;

      // Mock clicking on a vertex
      state = Line.select(state, SELECTED_LAYER_ID, line.id).updatedState;
      state = Vertex.beginDraggingVertex(state, SELECTED_LAYER_ID, originalVertexID, x, y).updatedState;
    });

    it('In the same axis, drags the vertex accross the axis', () => {
      const clonedState = cloneDeep(state); // To compare with the original vertex
      state = Vertex.updateDraggingVertex(clonedState, x + INCR, y).updatedState;

      const updatedVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[originalVertexID];
      expect(updatedVertex.x).toBe(originalVertex.x + INCR);
    });
    it('Outside of the same axis, is not dragged', () => {
      const originalState = state;

      state = Vertex.updateDraggingVertex(state, x, y + INCR).updatedState;
      const updatedVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[originalVertexID];

      expect(updatedVertex.y).toBe(originalVertex.y);
      expect(state).toBe(originalState);
    });

    it('Outside of the same axis, with all snaps disabled, is dragged', () => {
      state.snapMask = { SNAP_POINT: false, SNAP_SEGMENT: false };
      const clonedState = cloneDeep(state); // To compare with the original vertex

      state = Vertex.updateDraggingVertex(clonedState, x, y + INCR).updatedState;
      const updatedVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[originalVertexID];

      expect(updatedVertex.y).toBe(originalVertex.y + INCR);
    });
  });

  describe('beginDraggingVertex', () => {
    let state;

    const isValidLine = (state, line) => {
      const correctNumberOfVertices = line.vertices.length === 2 && line.auxVertices.length === 4;
      const allVertices = [...line.vertices, ...line.auxVertices];
      const allVerticesExists = allVertices.every(v => state.scene.layers[SELECTED_LAYER_ID].vertices[v]);
      return allVerticesExists && correctNumberOfVertices;
    };

    const vertexHasBeenDuplicated = (state, vertex) => {
      return Object.values(state.scene.layers[SELECTED_LAYER_ID].vertices).find(
        (v: VertexType) => v.x === vertex.x && v.y === vertex.y && v.id === vertex.id
      );
    };

    const linePoints = { x0: 10, y0: 10, x1: 20, y1: 10 };
    let initialLine;

    beforeEach(() => {
      // Setup a clean state with snaps enabled
      state = getCleanMockState();
      state.snapMask = DEFAULT_SNAP_MASK;

      // Create an horizontal line, like "-----"
      const { updatedState, line } = addLineToState(state, SeparatorsType.WALL, linePoints);
      state = updatedState;
      initialLine = line;
      // Mock clicking on a vertex
      state = Line.select(cloneDeep(state), SELECTED_LAYER_ID, line.id).updatedState;
    });

    it('Duplicates the vertex if it is shared as a main vertex in other line', () => {
      // Add a line with a shared main vertex
      const newLinePoints = { x0: linePoints.x1, y0: linePoints.y1, x1: linePoints.x1 + 10, y1: linePoints.y1 };
      const { updatedState, line: draggingLine } = addLineToState(state, SeparatorsType.WALL, newLinePoints);
      state = updatedState;
      const draggingVertexId = draggingLine.vertices[0]; // Same as initialLine.vertices[1]
      const draggingVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[draggingVertexId];
      const { x, y } = draggingVertex;

      // Initially both lines share vertices
      expect(initialLine.vertices.includes(draggingVertex.id)).toBeTruthy();
      expect(draggingLine.vertices.includes(draggingVertex.id)).toBeTruthy();

      // If we start dragging
      state = Vertex.beginDraggingVertex(cloneDeep(state), SELECTED_LAYER_ID, draggingVertexId, x, y).updatedState;

      const updatedInitialLine = state.scene.layers[SELECTED_LAYER_ID].lines[initialLine.id];
      const updatedDraggingLine = state.scene.layers[SELECTED_LAYER_ID].lines[draggingLine.id];
      // One has it, the other does not

      expect(updatedInitialLine.vertices.includes(draggingVertex.id)).toBeTruthy();
      expect(updatedDraggingLine.vertices.includes(draggingVertex.id)).toBeFalsy();

      // Both lines are valid
      expect(isValidLine(state, updatedInitialLine)).toBeTruthy();
      expect(isValidLine(state, updatedDraggingLine)).toBeTruthy();

      // And vertex is duplicated
      expect(vertexHasBeenDuplicated(state, draggingVertex)).toBeTruthy();
    });

    it('Duplicates the vertex if it is shared as an aux vertex', () => {
      // Add a line whose main vertex share with one of the aux vertex of the initial line
      const newLinePoints = { x0: 10, y0: 10, x1: 15, y1: 15 };

      const { updatedState, line: draggingLine } = addLineToState(state, SeparatorsType.WALL, newLinePoints);
      state = updatedState;

      const draggingVertexId = draggingLine.auxVertices[0]; // Same as initialLine.vertices[1]
      const draggingVertex = state.scene.layers[SELECTED_LAYER_ID].vertices[draggingVertexId];

      const { x, y } = draggingVertex;
      // Initially both lines share vertices (main vertex in one, aux in  the other)
      expect(initialLine.vertices.includes(draggingVertex.id)).toBeTruthy();
      expect(draggingLine.auxVertices.includes(draggingVertex.id)).toBeTruthy();

      // If we start dragging
      state = Vertex.beginDraggingVertex(cloneDeep(state), SELECTED_LAYER_ID, draggingVertexId, x, y).updatedState;
      const updatedInitialLine = state.scene.layers[SELECTED_LAYER_ID].lines[initialLine.id];
      const updatedDraggingLine = state.scene.layers[SELECTED_LAYER_ID].lines[draggingLine.id];

      // One has it, the other does not
      expect(updatedInitialLine.vertices.includes(draggingVertex.id)).toBeTruthy();
      expect(updatedDraggingLine.auxVertices.includes(draggingVertex.id)).toBeFalsy();

      // Both lines are valid
      expect(isValidLine(state, updatedInitialLine)).toBeTruthy();
      expect(isValidLine(state, updatedDraggingLine)).toBeTruthy();

      // And vertex is duplicated
      expect(vertexHasBeenDuplicated(state, draggingVertex)).toBeTruthy();
    });
  });
});
