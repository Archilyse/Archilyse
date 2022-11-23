import { isDraft } from 'immer';
import { Vertex as VertexModel } from '../models';
import * as GeometryUtils from '../utils/geometry';
import * as SnapSceneUtils from '../utils/snap-scene';
import * as SnapUtils from '../utils/snap';
import IDBroker from '../utils/id-broker';
import { EPSILON, MODE_DRAGGING_VERTEX } from '../constants';
import { AddVertexOptions, State, UpdatedStateObject, Vertex as VertexType } from '../types';
import getFastStateObject from '../utils/get-fast-state-object';
import Layer from './layer';
import Line from './line';

const isSnapFullyEnabled = state =>
  state.snapMask &&
  Object.keys(state.snapMask).length !== 0 &&
  Object.values(state.snapMask).every(snapOption => snapOption === true);

const isOrphanVertex = (state, layerID, vertex) => {
  if (!vertex.lines) return true;
  const layer = state.scene.layers[layerID];
  const isOrphan = vertex.lines.some(lineID => {
    const lineExists = Boolean(layer.lines[lineID]);
    return !lineExists;
  });
  return isOrphan;
};
class Vertex {
  static add(
    state,
    layerID,
    x,
    y,
    relatedPrototype,
    relatedID,
    options: AddVertexOptions = { force: false }
  ): UpdatedStateObject & { vertex: VertexType } {
    const originalScene = isDraft(state.scene)
      ? options?.fastStateObject?.scene || getFastStateObject(state).scene
      : state.scene;

    const scaledEpsilon = GeometryUtils.convertCMToPixels(state.scene.scale, EPSILON);
    const allVertices: VertexType[] = Object.values(originalScene.layers[layerID].vertices);
    let vertex = allVertices.find(vertex => {
      const sameLine = vertex.lines.every(lineID => lineID === relatedID);

      const samePoint = GeometryUtils.samePoints(vertex, { x, y }, scaledEpsilon);
      return samePoint && !sameLine;
    });

    if (vertex && !options.force) {
      let relatedIDs = vertex[relatedPrototype];
      if (!relatedIDs.includes(relatedID)) {
        relatedIDs = relatedIDs.concat(relatedID);
      }
      vertex = {
        ...vertex,
        [relatedPrototype]: relatedIDs,
      };
    } else {
      vertex = new VertexModel({
        id: IDBroker.acquireID(),
        name: 'Vertex',
        x: GeometryUtils.roundCoord(x),
        y: GeometryUtils.roundCoord(y),
        [relatedPrototype]: [relatedID],
      });
    }
    state.scene.layers[layerID].vertices[vertex.id] = vertex;

    return { updatedState: state, vertex };
  }

  static duplicate(state, layerID, originalVertex) {
    const { updatedState, vertex } = Vertex.add(
      state,
      layerID,
      originalVertex.x,
      originalVertex.y,
      'lines',
      null, // Add does not accept an array of lines, just an element
      { force: true }
    );
    state = updatedState;
    state.scene.layers[layerID].vertices[vertex.id].lines = originalVertex.lines;
    const newElement = state.scene.layers[layerID].vertices[vertex.id];
    return { updatedState: state, newElement };
  }

  static setAttributes(state, layerID, vertexID, vertexAttributes) {
    state.scene.layers[layerID].vertices[vertexID] = {
      ...state.scene.layers[layerID].vertices[vertexID],
      ...vertexAttributes,
    };

    return { updatedState: state };
  }

  static updateCoords(state, layerID, vertexID, x, y) {
    x = GeometryUtils.roundCoord(x);
    y = GeometryUtils.roundCoord(y);

    state = this.setAttributes(state, layerID, vertexID, { x, y }).updatedState;

    // We have to enforce the order of the main vertices, as the update may have change which one is bigger/smaller.
    const vertex = state.scene.layers[layerID].vertices[vertexID];
    vertex.lines.forEach(lineID => {
      state = Line.orderMainVertices(state, layerID, lineID).updatedState;
    });

    return { updatedState: state };
  }

  static addElement(state, layerID, vertexID, elementPrototype, elementID) {
    const elements = state.scene.layers[layerID].vertices[vertexID][elementPrototype];
    if (!elements.includes(elementID)) {
      const newElements = elements.concat(elementID);
      state.scene.layers[layerID].vertices[vertexID][elementPrototype] = newElements;
    }
    return { updatedState: state };
  }

  // @TODO: Update
  static removeElement(state, layerID, vertexID, elementPrototype, elementID) {
    const elementIndex = state
      .getIn(['scene', 'layers', layerID, 'vertices', vertexID, elementPrototype])
      .findIndex(el => el === elementID);
    if (elementIndex !== -1) {
      state = state.updateIn(['scene', 'layers', layerID, 'vertices', vertexID, elementPrototype], list =>
        list.remove(elementIndex)
      );
    }
    return { updatedState: state };
  }

  static select(state, layerID, vertexID) {
    state = Layer.selectElement(state, layerID, 'vertices', vertexID).updatedState;

    return { updatedState: state };
  }

  static unselect(state, layerID, vertexID) {
    state = state = Layer.unselect(state, layerID, 'vertices', vertexID).updatedState;

    return { updatedState: state };
  }

  static remove(state, layerID, vertexID, relatedPrototype = undefined, relatedID = undefined) {
    let vertex = state.scene.layers[layerID].vertices[vertexID];

    if (vertex) {
      const forceRemove = !relatedPrototype && !relatedID;
      if (!forceRemove) {
        vertex = {
          ...vertex,
          [relatedPrototype]: vertex[relatedPrototype].filter(ID => ID !== relatedID),
        };
      }

      const inUse = vertex.lines.length;
      if (forceRemove || !inUse) {
        state = this.unselect(state, layerID, vertexID).updatedState;
        delete state.scene.layers[layerID].vertices[vertexID];
      } else {
        state.scene.layers[layerID].vertices[vertexID] = vertex;
      }
      if (isOrphanVertex(state, layerID, vertex)) {
        console.error(
          `Orphan vertex ${vertex.id} detected
          \n Position: ${vertex.x}, ${vertex.y}.
          \n Vertex lines: ${vertex.lines.join(',')}
          \n Related prototype: "${relatedPrototype}"
          \n Related id:  ${relatedID}
          \n Current mode: ${state.mode}`
        );
      }
    }

    return { updatedState: state };
  }

  static duplicateSharedVertices(
    state: State,
    layerID: string,
    draggingVertex: VertexType,
    draggingLineId: string
  ): UpdatedStateObject {
    const otherLinesWithSameVertex: string[] = draggingVertex.lines.filter(lineId => lineId !== draggingLineId);

    const { x, y } = draggingVertex;
    const vertexOptions = { force: true };

    // Replace the vertex in the other lines  with a duplication of the dragging one
    otherLinesWithSameVertex.forEach(lineId => {
      const { updatedState, vertex: duplicatedVertex } = this.add(state, layerID, x, y, 'lines', lineId, vertexOptions);
      state = updatedState;
      state = Line.replaceVertices(state, layerID, lineId, duplicatedVertex, draggingVertex).updatedState;
    });

    // Erase the other lines from the vertex we are dragging
    state.scene.layers[layerID].vertices[draggingVertex.id].lines = [draggingLineId];
    return { updatedState: state };
  }

  static beginDraggingVertex(state, layerID, vertexID, x, y) {
    let snap = null;
    // Calculate snap elements so when clicking "near" a vertex, we drag that vertex (instead of the close x,y the user clicked)
    let snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(state.scene, [], state.snapMask, null, x, y);

    if (isSnapFullyEnabled(state)) {
      snap = SnapUtils.nearestSnap(snapElements, x, y, state.snapMask);
      if (snap) ({ x, y } = snap.point);
      const layer = state.scene.layers[layerID];
      snapElements = SnapUtils.addSnapLinesSameAxis(state.scene, { x, y }, layer);
    }

    const currentMode = state.mode;

    state.snapElements = snapElements;
    state.draggingSupport = {
      layerID,
      vertexID,
      previousMode: currentMode,
    };
    state.mode = MODE_DRAGGING_VERTEX;

    const [draggingLineId] = state.scene.layers[layerID].selected.lines;
    const draggingVertex = state.scene.layers[layerID].vertices[vertexID];
    const vertexHasMoreThanOneLine = draggingVertex.lines.length > 1;
    if (vertexHasMoreThanOneLine) {
      state = this.duplicateSharedVertices(state, layerID, draggingVertex, draggingLineId).updatedState;
    }

    return { updatedState: state };
  }

  static updateDraggingVertex(state, x, y) {
    const draggingSupport = state.draggingSupport;
    const layerID = draggingSupport.layerID;
    const [selectedLineId] = state.scene.layers[layerID].selected.lines;
    const snapElements = state.snapElements;

    let snap = null;
    if (isSnapFullyEnabled(state)) {
      snap = SnapUtils.nearestSnap(snapElements, x, y, state.snapMask);
      if (snap) {
        ({ x, y } = snap.point);
      } else {
        // We only allow dragging vertex accross the same axis snaps
        return { updatedState: state };
      }
    }

    const vertexID = draggingSupport.vertexID;
    state.scene.layers[layerID].vertices[vertexID].x = GeometryUtils.roundCoord(x);
    state.scene.layers[layerID].vertices[vertexID].y = GeometryUtils.roundCoord(y);

    const options = { adjustHoles: true, auxVerticesOptions: {} };
    const shouldReloadAreas = false;
    state = Line.recreateLineShape(state, layerID, selectedLineId, shouldReloadAreas, options).updatedState;

    return { updatedState: state };
  }

  static endDraggingVertex(state, x, y) {
    const draggingSupport = state.draggingSupport;
    const layerID = draggingSupport.layerID;
    const [selectedLineId] = state.scene.layers[layerID].selected.lines;

    state.mode = draggingSupport.previousMode;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.draggingSupport = null;

    state = Line.postprocess(state, layerID, selectedLineId).updatedState;
    state = Layer.detectAndUpdateAreas(state, layerID).updatedState;

    return { updatedState: state };
  }
}

export { Vertex as default };
