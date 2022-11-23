import { ProviderStorage } from 'archilyse-ui-components';
import { GeometryUtils, history, SnapSceneUtils, SnapUtils } from '../utils/export';
import { getRectParametersFromSelection } from '../utils/geometry';
import { RecreateLineShapeOptions, State, StorageCopyPaste, UpdatedStateObject, Vertex as VertexType } from '../types';
import { Hole as HoleModel, Item as ItemModel, Line as LineModel, Vertex as VertexModel } from '../models';
import { getSelectedLayer } from '../utils/state-utils';
import { MODE_COPY_PASTE, STORAGE } from '../constants';
import {
  detectElementsUnderSelection,
  findRepeatedVerticesForVertex,
  getCopiedElements,
  getSelectionCenter,
  getVerticesToTransform,
} from '../utils/copy-paste-utils';
import Project from './project';
import Layer from './layer';
import Line from './line';
import Hole from './hole';
import Vertex from './vertex';
import Item from './item';

const RECREATE_OPTIONS: RecreateLineShapeOptions = {
  auxVerticesOptions: {
    force: true,
    selectNewVertices: true,
  },
  adjustHoles: false,
};
class CopyPaste {
  static previousSelectionCenter = { x: undefined, y: undefined };
  static previousRotation = 0;

  static updateDraggingPosition(state: State, x, y): UpdatedStateObject {
    const selection = state.copyPaste.selection;
    const { width, height } = getRectParametersFromSelection(selection);

    // Adjust position so the cursor is always at the center of the rectangle
    const newDraggingPosition = {
      x: x - width / 2,
      y: y - height / 2,
    };

    state.copyPaste.selection.draggingPosition = newDraggingPosition;

    return { updatedState: state };
  }

  static clearSelection(state: State): UpdatedStateObject {
    this.previousRotation = 0;
    this.previousSelectionCenter = { x: undefined, y: undefined };
    ProviderStorage.delete(STORAGE.COPY_PASTE);

    state.copyPaste = {
      drawing: false,
      dragging: false,
      rotating: false,
      selection: {
        lines: [],
        items: [],
        holes: [],
        startPosition: { x: -1, y: -1 },
        endPosition: { x: -1, y: -1 },
        draggingPosition: { x: -1, y: -1 },
        rotation: undefined,
      },
    };

    return { updatedState: state };
  }

  static deleteCurrentSelection(state: State): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const selection = state.copyPaste.selection;
    if (selection?.lines?.length > 0 || selection?.items?.length > 0) {
      // Lines remove also any holes on it
      selection.lines?.forEach(lineID => {
        state = Line.remove(state, layerID, lineID).updatedState;
      });

      selection.items?.forEach(itemID => {
        state = Item.remove(state, layerID, itemID).updatedState;
      });
      state = this.clearSelection(state).updatedState;
    }

    return { updatedState: state };
  }

  static cloneElements(
    state: State,
    layerID,
    originalElements,
    ElementClass
  ): UpdatedStateObject & { clonedElements: any } {
    const clonedElements = [];
    originalElements.forEach(originalElement => {
      const { updatedState, newElement } = ElementClass.duplicate(state, layerID, originalElement);
      clonedElements.push(newElement);
      state = updatedState;
    });
    return { updatedState: state, clonedElements };
  }

  static selectElements(state: State, layerID, elements, ElementClass): UpdatedStateObject {
    elements.forEach(element => {
      state = ElementClass.select(state, layerID, element.id, { unselectAllBefore: false }).updatedState;
    });
    return { updatedState: state };
  }

  // @TODO: Add unit test
  static cloneAndSelectElements(state: State, layerID, originalLines, originalItems): UpdatedStateObject {
    state = Project.unselectAll(state).updatedState;

    // Line & the holes on it
    const { updatedState, clonedElements: clonedLines } = this.cloneElements(state, layerID, originalLines, Line);
    state = updatedState;
    state = this.selectElements(state, layerID, clonedLines, Line).updatedState;
    const clonedLineIDs = clonedLines.map(line => line.id);
    state.copyPaste.selection.lines = clonedLineIDs;

    // Items
    const { updatedState: stateAfterItemsClone, clonedElements: clonedItems } = this.cloneElements(
      state,
      layerID,
      originalItems,
      Item
    );
    state = stateAfterItemsClone;
    state = this.selectElements(state, layerID, clonedItems, Item).updatedState;
    const clonedItemIds = clonedItems.map(item => item.id);

    state.copyPaste.selection.items = clonedItemIds;

    // Holes (selection only, they are cloned with the lines)
    const layer = getSelectedLayer(state.scene);
    const clonedHoles = clonedLines.reduce((accum, line) => {
      const lineHoles = line.holes.map(holeID => layer.holes[holeID]);
      return [...accum, ...lineHoles];
    }, []);
    state = this.selectElements(state, layerID, clonedHoles, Hole).updatedState;
    const clonedHoleIds = clonedHoles.map(hole => hole.id);
    state.copyPaste.selection.holes = clonedHoleIds;

    return { updatedState: state };
  }

  static beginCopyPasteSelection(state: State, action): UpdatedStateObject {
    state = this.deleteCurrentSelection(state).updatedState;

    const { x, y } = action.payload;

    state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
    state.copyPaste.drawing = true;
    state.copyPaste.selection.rotation = 0;
    state.copyPaste.selection.startPosition.x = x;
    state.copyPaste.selection.startPosition.y = y;

    return { updatedState: state };
  }

  static updateCopyPasteSelection(state: State, action): UpdatedStateObject {
    const { x, y } = action.payload;

    state.copyPaste.selection.endPosition.x = x;
    state.copyPaste.selection.endPosition.y = y;

    return { updatedState: state };
  }

  static endCopyPasteSelection(state: State, action): UpdatedStateObject {
    const { x, y } = action.payload;

    state.copyPaste.drawing = false;

    state.copyPaste.selection.endPosition.x = x;
    state.copyPaste.selection.endPosition.y = y;

    const layerID = state.scene.selectedLayer;
    const selection = state.copyPaste.selection;
    const { items, lines } = detectElementsUnderSelection(state, layerID, selection);
    state = this.cloneAndSelectElements(state, layerID, lines, items).updatedState;

    // We need to make the copy before merge the vertices to be able to replicate it while restoring it later
    const copiedElements = getCopiedElements(state);
    const updatedSelection = state.copyPaste.selection;
    const copy: StorageCopyPaste = {
      elements: copiedElements,
      selection: updatedSelection,
      planId: state.planInfo.id,
    };
    ProviderStorage.set(STORAGE.COPY_PASTE, JSON.stringify(copy));

    state = this.mergeEqualVertices(state).updatedState;
    return { updatedState: state };
  }

  static mergeEqualVertices(state: State): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const copyPastedVertices = Object.values(getVerticesToTransform(state));
    const replacedVertices = {};

    copyPastedVertices.forEach(vertex => {
      const alreadyReplaced = replacedVertices[vertex.id];
      if (alreadyReplaced) return;

      const repeatedVertices = findRepeatedVerticesForVertex(state, layerID, copyPastedVertices, vertex);
      repeatedVertices.forEach(repeatedVertex => {
        repeatedVertex.lines.forEach(lineID => {
          state = Line.replaceVertices(state, layerID, lineID, vertex, repeatedVertex).updatedState;
        });
        replacedVertices[repeatedVertex.id] = true;
      });
    });
    return { updatedState: state };
  }

  static beginDraggingCopyPasteSelection(state: State, action): UpdatedStateObject {
    const { x, y } = action.payload;

    state.copyPaste.dragging = true;
    state = this.updateDraggingPosition(state, x, y).updatedState;
    this.previousSelectionCenter = { x: undefined, y: undefined };

    return { updatedState: state };
  }

  static updateDraggingCopyPasteSelection(state: State, action): UpdatedStateObject {
    const { x, y } = action.payload;
    const snapElements = SnapSceneUtils.sceneSnapNearestCopyPasteElements(
      state.scene,
      state.snapMask,
      state.copyPaste.selection,
      x,
      y
    );

    state = this.updateDraggingPosition(state, x, y).updatedState;
    state = this.translateCopyPasteSelectionFromDocument(state).updatedState;

    state.snapElements = snapElements;

    return { updatedState: state };
  }

  static endDraggingCopyPasteSelection(state: State, action): UpdatedStateObject {
    let { x, y } = action.payload;

    state.copyPaste.dragging = false;

    const snapElements = SnapSceneUtils.sceneSnapNearestCopyPasteElements(
      state.scene,
      state.snapMask,
      state.copyPaste.selection,
      x,
      y
    );

    const snapMaskIsNotEmpty = Object.keys(state.snapMask).length !== 0;
    const isSnapEnabled = state.snapMask && snapMaskIsNotEmpty;
    if (isSnapEnabled) {
      const snap = SnapUtils.nearestCopyPasteSnap(state, snapElements, { x, y });
      if (snap) ({ x, y } = snap.point);
    }

    state = this.updateDraggingPosition(state, x, y).updatedState;
    state = this.translateCopyPasteSelectionFromDocument(state).updatedState;

    state.snapElements = [];

    return { updatedState: state };
  }

  static rotateCopyPasteSelectionFromDocument(state: State): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const selection = state.copyPaste.selection;
    const { rotation } = selection;
    const selectionCenter = getSelectionCenter(selection);

    // Lines
    // We have to get the rotation previous the last known one, to know how much we have to "rotate" from our
    // last position, as otherwise we are going to apply the rotation from the initial position all the time.
    const currentRotation = rotation - this.previousRotation;
    const verticesToTransform = getVerticesToTransform(state);
    Object.values(verticesToTransform).forEach((vertex: VertexType) => {
      const vertexElem = document.querySelector(`g[data-id="${vertex.id}"]`);
      const prevVertexCoords = {
        x: vertex.x,
        y: vertex.y,
      };
      const vertexCoords = (vertexElem && JSON.parse(vertexElem.getAttribute('data-coords'))) || prevVertexCoords;
      const { x: rotatedX, y: rotatedY } = GeometryUtils.rotatePointAroundPoint(
        vertexCoords.x,
        vertexCoords.y,
        selectionCenter.x,
        selectionCenter.y,
        currentRotation
      );
      state = Vertex.setAttributes(state, layerID, vertex.id, { x: rotatedX, y: rotatedY }).updatedState;
    });

    const layer = getSelectedLayer(state.scene);

    const copyPastedLines = state.copyPaste.selection.lines;
    const shouldUpdateAuxVertices = false;
    const shouldReloadAreas = false;
    copyPastedLines.forEach(lineID => {
      state = Line.recreateLineShape(
        state,
        layerID,
        lineID,
        shouldReloadAreas,
        RECREATE_OPTIONS,
        shouldUpdateAuxVertices
      ).updatedState;
    });

    // Items
    const copyPastedItems = state.copyPaste.selection.items;
    copyPastedItems.forEach(itemID => {
      const item = document.querySelector(`g[data-id="${itemID}"]`);
      const { x, y } = layer.items[itemID];
      const prevItemCoords = { x, y };
      const itemCoords = (item && JSON.parse(item.getAttribute('data-coords'))) || prevItemCoords;
      const { x: rotatedX, y: rotatedY } = GeometryUtils.rotatePointAroundPoint(
        itemCoords.x,
        itemCoords.y,
        selectionCenter.x,
        selectionCenter.y,
        currentRotation
      );

      state = Item.setAttributes(state, layerID, itemID, { rotation, x: rotatedX, y: rotatedY }).updatedState;
    });

    // Holes
    const copyPastedHoles = state.copyPaste.selection.holes;
    copyPastedHoles.forEach(holeID => {
      const hole = layer.holes[holeID];
      const holeElem = document.querySelector(`g[data-id="${holeID}"]`);
      const polygon = holeElem?.querySelector('g polygon');
      const coordinates = polygon && JSON.parse(polygon.getAttribute('data-coords'));
      const [polygonCoords] = coordinates || hole.coordinates;
      const newHoleCoords = polygonCoords.map(([x, y]) => {
        const { x: rotatedX, y: rotatedY } = GeometryUtils.rotatePointAroundPoint(
          x,
          y,
          selectionCenter.x,
          selectionCenter.y,
          currentRotation
        );
        return [rotatedX, rotatedY];
      });
      state.scene.layers[layer.id].holes[hole.id].coordinates = [newHoleCoords];

      if (hole.door_sweeping_points) {
        state = Hole.updateDoorSweepingPoints(state, holeID).updatedState;
      }
    });

    return { updatedState: state };
  }

  static translateCopyPasteSelectionFromDocument(state: State): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const selection = state.copyPaste.selection;
    const selectionCenter = getSelectionCenter(selection);
    const deltaX = this.previousSelectionCenter.x ? selectionCenter.x - this.previousSelectionCenter.x : 0;
    const deltaY = this.previousSelectionCenter.y ? selectionCenter.y - this.previousSelectionCenter.y : 0;

    // Lines
    const verticesToTransform = getVerticesToTransform(state);
    Object.values(verticesToTransform).forEach((vertex: VertexType) => {
      const vertexElem = document.querySelector(`g[data-id="${vertex.id}"]`);
      const prevVertexCoords = {
        x: vertex.x,
        y: vertex.y,
      };
      const vertexCoords = (vertexElem && JSON.parse(vertexElem?.getAttribute('data-coords'))) || prevVertexCoords;
      const translatedX = vertexCoords.x + deltaX;
      const translatedY = vertexCoords.y + deltaY;
      state = Vertex.setAttributes(state, layerID, vertex.id, { x: translatedX, y: translatedY }).updatedState;
    });

    const copyPastedLines = state.copyPaste.selection.lines;
    const shouldUpdateAuxVertices = false;
    const shouldReloadAreas = false;
    copyPastedLines.forEach(lineID => {
      state = Line.recreateLineShape(
        state,
        layerID,
        lineID,
        shouldReloadAreas,
        RECREATE_OPTIONS,
        shouldUpdateAuxVertices
      ).updatedState;
    });

    // Items
    const layer = getSelectedLayer(state.scene);
    const copyPastedItems = state.copyPaste.selection.items;
    copyPastedItems.forEach(itemID => {
      const item = document.querySelector(`g[data-id="${itemID}"]`);
      const prevItemCoords = {
        x: layer.items[itemID].x,
        y: layer.items[itemID].y,
      };
      const itemCoords = (item && JSON.parse(item.getAttribute('data-coords'))) || prevItemCoords;
      const translatedX = itemCoords.x + deltaX;
      const translatedY = itemCoords.y + deltaY;
      state = Item.setAttributes(state, layerID, itemID, { x: translatedX, y: translatedY }).updatedState;
    });

    // Holes
    const copyPastedHoles = state.copyPaste.selection.holes;
    copyPastedHoles.forEach(holeID => {
      const hole = layer.holes[holeID];
      const holeElem = document.querySelector(`g[data-id="${holeID}"]`);
      const polygon = holeElem?.querySelector('g polygon');
      const coordinates = polygon && JSON.parse(polygon.getAttribute('data-coords'));
      const [polygonCoords] = coordinates || hole.coordinates;
      const newHoleCoordinates = polygonCoords.map(([x, y]) => {
        const translatedX = x + deltaX;
        const translatedY = y + deltaY;
        return [translatedX, translatedY];
      });
      state.scene.layers[layer.id].holes[hole.id].coordinates = [newHoleCoordinates];

      if (hole.door_sweeping_points) {
        state = Hole.updateDoorSweepingPoints(state, holeID).updatedState;
      }
    });

    this.previousSelectionCenter = selectionCenter;
    return { updatedState: state };
  }

  static restoreCopyPasteFromAnotherPlan(state: State): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;

    const copy = JSON.parse(ProviderStorage.get(STORAGE.COPY_PASTE));
    state.mode = MODE_COPY_PASTE;
    state.copyPaste.selection = copy.selection;

    const verticesToRestorePerID = copy.elements.vertices.reduce((accum, vertex) => {
      accum[vertex.id] = new VertexModel(vertex);
      return accum;
    }, {});

    const holesToRestorePerID = copy.elements.holes.reduce((accum, hole) => {
      hole.line = undefined; // To explicitly create the hole without a line
      accum[hole.id] = new HoleModel(hole);
      return accum;
    }, {});

    /*
      To clone a line we need its vertices so we have to first:
      1. Clone the vertices from the copied ones
      2. Update the "linesToRestore" with this new vertices
      3. Clone the lines with this new vertices
      4. Erase the cloned vertices

      In the same way, to clone a hole we need the line so:
      1. Clone the hole separately
      2. Update line - hole relationship
      3. When cloning in `cloneAndSelectElements` we will clone every hole

  */
    const linesToRestore = copy.elements.lines.map(line => {
      const originalLineVertices = line.vertices.map(vertexID => verticesToRestorePerID[vertexID]);

      const mainCloneResult = this.cloneElements(state, layerID, originalLineVertices, Vertex);
      state = mainCloneResult.updatedState;

      const originalAuxVertices = line.auxVertices.map(vertexID => verticesToRestorePerID[vertexID]);
      const auxCloneResult = this.cloneElements(state, layerID, originalAuxVertices, Vertex);
      state = auxCloneResult.updatedState;

      const originalLineHoles = line.holes.map(holeID => holesToRestorePerID[holeID]);
      const holeCloneResult = this.cloneElements(state, layerID, originalLineHoles, Hole);
      state = holeCloneResult.updatedState;

      return new LineModel({
        ...line,
        holes: holeCloneResult.clonedElements.map(hole => hole.id),
        vertices: mainCloneResult.clonedElements.map(vertex => vertex.id),
        auxVertices: auxCloneResult.clonedElements.map(vertex => vertex.id),
      });
    });

    const itemsToRestore = copy.elements.items.map(item => new ItemModel(item));

    state = this.cloneAndSelectElements(state, layerID, linesToRestore, itemsToRestore).updatedState;
    state = this.mergeEqualVertices(state).updatedState;

    // Now we have to delete the vertices & holes created in linesToRestore, since those have been already cloned while cloning the lines
    linesToRestore.forEach(line => {
      line.vertices.forEach(vertexID => {
        state = Vertex.remove(state, layerID, vertexID, 'lines', line.id).updatedState;
      });
      line.auxVertices.forEach(vertexID => {
        state = Vertex.remove(state, layerID, vertexID, 'lines', line.id).updatedState;
      });
      line.holes.forEach(holeID => {
        state = Hole.remove(state, layerID, holeID).updatedState;
      });
    });

    ProviderStorage.delete(STORAGE.COPY_PASTE);

    return { updatedState: state };
  }
  static saveCopyPasteSelection(state: State): UpdatedStateObject {
    state = this.clearSelection(state).updatedState;

    // New areas could have been created
    const layerID = state.scene.selectedLayer;
    state = Layer.detectAndUpdateAreas(state, layerID).updatedState;

    state = Project.unselectAll(state).updatedState;
    return { updatedState: state };
  }

  static beginRotatingCopyPasteSelection(state: State): UpdatedStateObject {
    state.copyPaste.rotating = true;

    return { updatedState: state };
  }

  static updateRotatingCopyPasteSelection(state: State, action): UpdatedStateObject {
    const { x, y } = action.payload;
    const selection = state.copyPaste.selection;
    const selectionCenter = getSelectionCenter(selection);

    const deltaX = x - selectionCenter.x;
    const deltaY = y - selectionCenter.y;
    let rotation = (Math.atan2(deltaY, deltaX) * 180) / Math.PI - 90;

    if (-5 < rotation && rotation < 5) rotation = 0;
    if (-95 < rotation && rotation < -85) rotation = -90;
    if (-185 < rotation && rotation < -175) rotation = -180;
    if (85 < rotation && rotation < 90) rotation = 90;
    if (-270 < rotation && rotation < -265) rotation = 90;

    state.copyPaste.selection.rotation = rotation;
    state = this.rotateCopyPasteSelectionFromDocument(state).updatedState;

    this.previousRotation = rotation;

    return { updatedState: state };
  }

  static endRotatingCopyPasteSelection(state: State, action): UpdatedStateObject {
    state.copyPaste.rotating = false;
    state = this.updateRotatingCopyPasteSelection(state, action).updatedState;

    return { updatedState: state };
  }
}

export { CopyPaste as default };
