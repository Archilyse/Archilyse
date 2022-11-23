import { detectElementsUnderSelection } from '../utils/copy-paste-utils';
import { getSelectedLayer } from '../utils/state-utils';
import Project from './project';
import Line from './line';
import Hole from './hole';
import Item from './item';

class RectangleSelectTool {
  static clearSelection(state) {
    state.rectangleTool = {
      drawing: false,
      selection: {
        startPosition: { x: -1, y: -1 },
        endPosition: { x: -1, y: -1 },
        draggingPosition: { x: -1, y: -1 },
      },
    };
    return { updatedState: state };
  }

  static selectElements(state, layerID, elements, ElementClass) {
    elements.forEach(element => {
      state = ElementClass.select(state, layerID, element.id, { unselectAllBefore: false }).updatedState;
    });
    return { updatedState: state };
  }

  static beginRectangleSelection(state, action) {
    // unselect all annotations when begin drawing
    state = Project.unselectAll(state).updatedState;
    const { x, y } = action.payload;

    state.rectangleTool.drawing = true;
    state.rectangleTool.selection.startPosition = { x, y };

    return { updatedState: state };
  }

  static updateRectangleSelection(state, action) {
    const { x, y } = action.payload;
    state.rectangleTool.selection.endPosition = { x, y };

    return { updatedState: state };
  }

  static endRectangleSelection(state, action) {
    const { x, y } = action.payload;

    state.rectangleTool.drawing = false;
    state.rectangleTool.selection.endPosition = { x, y };

    const layerID = state.scene.selectedLayer;
    const selection = state.rectangleTool.selection;
    const { items, lines } = detectElementsUnderSelection(state, layerID, selection);

    // Select lines
    state = this.selectElements(state, layerID, lines, Line).updatedState;
    // Select items
    state = this.selectElements(state, layerID, items, Item).updatedState;

    // Select holes
    const layer = getSelectedLayer(state.scene);
    const holes = lines.reduce((accum: Array<any>, line: any) => {
      const lineHoles = line.holes.map(holeID => layer.holes[holeID]);
      return [...accum, ...lineHoles];
    }, []);
    state = this.selectElements(state, layerID, holes, Hole).updatedState;

    // remove rectangle selection at the end
    state = this.clearSelection(state).updatedState;

    return { updatedState: state };
  }
}

export { RectangleSelectTool as default };
