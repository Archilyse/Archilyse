import {
  MODE_COPY_PASTE,
  MODE_DRAGGING_ITEM,
  MODE_DRAWING_HOLE,
  MODE_DRAWING_ITEM,
  MODE_DRAWING_LINE,
  MODE_IDLE,
  MODE_RECTANGLE_TOOL,
  MODE_ROTATING_ITEM,
  SeparatorsType,
} from '../constants';
import { Catalog, HistoryStructure, Scene, State } from '../models';
import hasCopyPasteBeenDragged from '../utils/has-copy-paste-been-dragged';
import isScaling from '../utils/is-scaling';
import getProjectHashCode from '../utils/get-project-hash-code';
import * as history from '../utils/history';
import { Line as LineType, Scene as SceneType, State as StateType, UpdatedStateObject } from '../types';
import { ProviderMetrics } from '../providers';
import CopyPaste from './copy-paste';
import RectangleSelectTool from './rectangle-tool';
import Layer from './layer';
import Line from './line';
import Hole from './hole';
import Item from './item';

const sortErrorsByCoordinates = (errorA, errorB) => {
  const aCoordinates = Number(errorA.position.coordinates.join('').replace('.', ''));
  const bCoordinates = Number(errorB.position.coordinates.join('').replace('.', ''));
  return aCoordinates - bCoordinates;
};

export default class Project {
  static setAlterate(state: StateType, alterate): UpdatedStateObject {
    state.alterate = alterate;

    return { updatedState: state };
  }

  static newProject(state: StateType): UpdatedStateObject {
    state = new State({ viewer2D: state.viewer2D });

    return { updatedState: state };
  }

  //TODO set centered to false if when scene isn't centered
  static fitScreen(state) {
    const isCentered = state.centered ? false : true;
    state.centered = isCentered;
    return { updatedState: state };
  }

  static loadProject(state: StateType, sceneJSON: SceneType): UpdatedStateObject {
    // sceneJSON comes from the backend with 0 elements selected of each type
    // setting previous selected elements
    if (sceneJSON) {
      // This if fixes a unit test. (general.test.tsx)
      const selectedLayer = state.scene.selectedLayer;
      const selectedElements = state.scene.layers[selectedLayer]?.selected;
      sceneJSON.layers[selectedLayer].selected = selectedElements;
    }

    const scene = new Scene(sceneJSON);

    state.scene = scene;
    state.sceneHistory = new HistoryStructure({ first: scene, last: scene });

    return { updatedState: state };
  }

  static setProjectHashCode(state: StateType): UpdatedStateObject {
    state.projectHashCode = getProjectHashCode(state);

    return { updatedState: state };
  }

  static setProperties(state: StateType, layerID: string, properties): UpdatedStateObject {
    state = Layer.setPropertiesOnSelected(state, layerID, properties).updatedState;

    return { updatedState: state };
  }

  static updateProperties(state: StateType, layerID: string, properties): UpdatedStateObject {
    state = Layer.updatePropertiesOnSelected(state, layerID, properties).updatedState;

    return { updatedState: state };
  }

  static setItemsAttributes(state: State, attributes): UpdatedStateObject {
    //TODO apply only to items
    Object.values(state.scene.layers).forEach(layer => {
      state = Layer.setAttributesOnSelected(state, layer.id, attributes).updatedState;
    });

    return { updatedState: state };
  }

  static setLinesAttributes(state: StateType, attributes): UpdatedStateObject {
    //TODO apply only to lines
    Object.values(state.scene.layers).forEach(layer => {
      state = Layer.setAttributesOnSelected(state, layer.id, attributes).updatedState;
    });

    return { updatedState: state };
  }

  static setHolesAttributes(state: StateType, attributes): UpdatedStateObject {
    //TODO apply only to holes
    Object.values(state.scene.layers).forEach(layer => {
      state = Layer.setAttributesOnSelected(state, layer.id, attributes).updatedState;
    });

    return { updatedState: state };
  }

  static unselectAll(state: StateType): UpdatedStateObject {
    Object.keys(state.scene.layers).map(layerID => {
      state = Layer.unselectAll(state, layerID).updatedState;
    });
    const updatedState = state;
    return { updatedState };
  }

  static remove(state: StateType): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    const { lines: selectedLines, holes: selectedHoles, items: selectedItems } = state.scene.layers[
      selectedLayer
    ].selected;

    state = Layer.unselectAll(state, selectedLayer).updatedState;

    selectedHoles.forEach(holeID => {
      state = Hole.remove(state, selectedLayer, holeID).updatedState;
    });
    selectedLines.forEach(lineID => {
      state = Line.remove(state, selectedLayer, lineID).updatedState;
    });
    selectedItems.forEach(itemID => {
      state = Item.remove(state, selectedLayer, itemID).updatedState;
    });

    return { updatedState: state };
  }

  static undo(state: StateType): UpdatedStateObject {
    let sceneHistory = state.sceneHistory;

    if (state.mode === MODE_COPY_PASTE) {
      state = CopyPaste.deleteCurrentSelection(state).updatedState;
    }
    if (sceneHistory.list.length === 0) {
      return { updatedState: state };
    }

    if (state.scene === sceneHistory.last && sceneHistory.list.length > 1) {
      sceneHistory = history.historyPop(sceneHistory);
    }

    state.mode = MODE_IDLE;
    state.scene = sceneHistory.last;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.sceneHistory = history.historyPop(sceneHistory);

    ProviderMetrics.clearTrackedEvents();
    return { updatedState: state };
  }

  static rollback(state: StateType): UpdatedStateObject {
    if (
      [MODE_DRAWING_LINE, MODE_DRAWING_HOLE, MODE_DRAWING_ITEM, MODE_DRAGGING_ITEM, MODE_ROTATING_ITEM].includes(
        state.mode
      )
    ) {
      state = this.undo(state).updatedState;
    }

    if (state.mode === MODE_COPY_PASTE) {
      const selection = state.copyPaste.selection;
      const selectionBeingModified =
        (selection.startPosition && selection.startPosition.x !== -1) ||
        hasCopyPasteBeenDragged(selection.draggingPosition);

      if (selectionBeingModified) state = this.undo(state).updatedState;
    }
    state = this.unselectAll(state).updatedState;

    state.mode = MODE_IDLE;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.draggingSupport = {};
    state.rotatingSupport = {};

    if (isScaling(state)) {
      state = Line.selectToolDrawingLine(state, SeparatorsType.SCALE_TOOL).updatedState;
    } else {
      state.drawingSupport = {};
    }
    return { updatedState: state };
  }

  static removeScalingLines(state: StateType): UpdatedStateObject {
    const layerID = state.scene.selectedLayer;
    const lines: LineType[] = Object.values(state.scene.layers[layerID].lines);
    lines
      .filter(line => line.type === SeparatorsType.SCALE_TOOL)

      .forEach(line => {
        state = Line.remove(state, layerID, line.id).updatedState;
      });
    return { updatedState: state };
  }

  static enableScaling(state: StateType): UpdatedStateObject {
    state = Line.selectToolDrawingLine(state, SeparatorsType.SCALE_TOOL).updatedState;
    state = this.removeScalingLines(state).updatedState;
    return { updatedState: state };
  }

  static disableScaling(state: StateType): UpdatedStateObject {
    state = this.setScaleToolProperties(state, { distance: 0, areaSize: 0, userHasChangedMeasures: false })
      .updatedState;

    state = this.unselectAll(state).updatedState;

    state.mode = MODE_IDLE;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.drawingSupport = {};

    state = this.removeScalingLines(state).updatedState;
    return { updatedState: state };
  }

  static clearScaleDrawing(state: StateType): UpdatedStateObject {
    // 1. Get a clean new state
    state = this.disableScaling(state).updatedState;
    // 2. Start drawing a scale line again (measures are not erased because they are in the <PanelScale /> local satate)
    state = this.enableScaling(state).updatedState;
    return { updatedState: state };
  }

  // @TODO: Probably can be deleted
  static setProjectProperties(state: StateType, properties): UpdatedStateObject {
    state.scene = { ...state.scene, ...properties };
    state.mode = MODE_IDLE;
    return { updatedState: state };
  }

  static setScaleToolProperties(state: StateType, properties): UpdatedStateObject {
    state.scaleTool = { ...state.scaleTool, ...properties };

    return { updatedState: state };
  }

  // @TODO: Probably can be deleted
  static setSceneProperties(state, properties) {
    state.scene = { ...state.scene, ...properties };

    return { updatedState: state };
  }

  static initCatalog(state, catalog): UpdatedStateObject {
    state.catalog = new Catalog(catalog);

    return { updatedState: state };
  }

  static toggleCatalogToolbar(state): UpdatedStateObject {
    const catalogToolbarOpened = state.catalogToolbarOpened;
    state.catalogToolbarOpened = !catalogToolbarOpened;

    return { updatedState: state };
  }

  // if no mask argument is provided then
  // both values will be assigned false/true
  static toggleSnap(state, mask): UpdatedStateObject {
    const SNAP_POINT = state.snapMask.SNAP_POINT;
    const SNAP_SEGMENT = state.snapMask.SNAP_SEGMENT;

    const nextBooleanVal = !(SNAP_POINT || SNAP_SEGMENT);
    mask = mask || {
      SNAP_POINT: nextBooleanVal,
      SNAP_SEGMENT: nextBooleanVal,
    };

    state.snapMask = mask;

    return { updatedState: state };
  }

  static toggleShowSnapElements(state): UpdatedStateObject {
    const currentShowSnapElements = state.showSnapElements;
    state.showSnapElements = !currentShowSnapElements;

    return { updatedState: state };
  }

  // @TODO: Delete, unused
  static throwError(state, error): UpdatedStateObject {
    state = state.set(
      'errors',
      state.get('errors').push({
        date: Date.now(),
        error,
      })
    );

    return { updatedState: state };
  }

  // @TODO: Delete, unused
  static throwWarning(state, warning): UpdatedStateObject {
    state = state.set(
      'warnings',
      state.warnings.push({
        date: Date.now(),
        warning,
      })
    );

    return { updatedState: state };
  }

  // @TODO: Delete, unused
  static copyProperties(state, properties): UpdatedStateObject {
    state = state.set('clipboardProperties', properties);

    return { updatedState: state };
  }

  static pasteProperties(state): UpdatedStateObject {
    state = this.updateProperties(state, state.scene.selectedLayer, state.clipboardProperties).updatedState;

    return { updatedState: state };
  }

  // @TODO: Delete, unused
  static pushLastSelectedCatalogElementToHistory(state, element): UpdatedStateObject {
    let currHistory = state.selectedElementsHistory;

    const previousPosition = currHistory.findIndex(el => el.name === element.name);
    if (previousPosition !== -1) {
      currHistory = currHistory.splice(previousPosition, 1);
    }
    currHistory = currHistory.splice(0, 0, element);

    state.selectedElementsHistory = currHistory;
    return { updatedState: state };
  }

  static setMode(state, mode): UpdatedStateObject {
    const currentMode = state.mode;
    if (currentMode === MODE_COPY_PASTE) {
      state = CopyPaste.deleteCurrentSelection(state).updatedState;
    }
    if (currentMode === MODE_RECTANGLE_TOOL) {
      state = RectangleSelectTool.clearSelection(state).updatedState;
    }

    state.mode = mode;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.drawingSupport = {};

    return { updatedState: state };
  }

  static setHighlightedError(state, errorObjectId): UpdatedStateObject {
    state.highlightedError = errorObjectId;

    return { updatedState: state };
  }

  static setValidationErrors(state, errors): UpdatedStateObject {
    // We need to keep same visual order when new/existing errors arrives from API
    const sortedErrors = errors.sort(sortErrorsByCoordinates);
    state.validationErrors = sortedErrors;

    return { updatedState: state };
  }

  static regenerateAreas(state: StateType): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    state = Layer.detectAndUpdateAreas(state, selectedLayer).updatedState;
    return { updatedState: state };
  }

  static setAnnotationFinished(state: StateType, annotationFinished): UpdatedStateObject {
    state.annotationFinished = annotationFinished;

    return { updatedState: state };
  }

  static mustImportAnnotations(state: StateType, annotationFinished): UpdatedStateObject {
    state.mustImportAnnotations = annotationFinished;

    return { updatedState: state };
  }

  static setSceneDimensions(state: StateType, dimensions): UpdatedStateObject {
    state.scene.width = dimensions.width;
    state.scene.height = dimensions.height;

    return { updatedState: state };
  }

  static setBackgroundDimensions(state: StateType, dimensions): UpdatedStateObject {
    state.scene.background.width = dimensions.width;
    state.scene.background.height = dimensions.height;

    return { updatedState: state };
  }

  static setBackgroundRotation(state: StateType, { rotation }): UpdatedStateObject {
    state.scene.background.rotation = rotation;

    return { updatedState: state };
  }

  static setBackgroundShift(state: StateType, { shift }): UpdatedStateObject {
    state.scene.background.shift = shift;

    return { updatedState: state };
  }

  static setShowBackgroundOnly(state, showBackgroundOnly): UpdatedStateObject {
    state.showBackgroundOnly = showBackgroundOnly;

    return { updatedState: state };
  }

  static setScaleValidated(state: StateType, scaleValidated): UpdatedStateObject {
    state.scaleValidated = scaleValidated;

    return { updatedState: state };
  }

  static setPlanInfo(state: StateType, plan): UpdatedStateObject {
    state.planInfo = plan;

    return { updatedState: state };
  }

  static showSnackbar(state: StateType, { message, severity, duration }): UpdatedStateObject {
    const snackbarState = { open: true, message, severity, duration };
    state.snackbar = snackbarState;

    return { updatedState: state };
  }

  static closeSnackbar(state: StateType): UpdatedStateObject {
    const snackbarState = { open: false, message: null, severity: '', duration: undefined };
    state.snackbar = snackbarState;

    return { updatedState: state };
  }
}
