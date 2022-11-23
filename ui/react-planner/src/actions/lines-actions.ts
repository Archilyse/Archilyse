import {
  BEGIN_DRAWING_LINE,
  CHANGE_LINE_TYPE,
  CHANGE_LINES_TYPE,
  CHANGE_REFERENCE_LINE,
  DECREASE_WIDTH_SELECTED_WALLS,
  END_DRAWING_LINE,
  INCREASE_WIDTH_SELECTED_WALLS,
  SELECT_LINE,
  SELECT_TOOL_DRAWING_LINE,
  UNSELECT_LINE,
  UPDATE_DRAWING_LINE,
} from '../constants';

export function selectLine(layerID, lineID) {
  return {
    type: SELECT_LINE,
    layerID,
    lineID,
  };
}

export function unselectLine(layerID, lineID) {
  return {
    type: UNSELECT_LINE,
    layerID,
    lineID,
  };
}

export function selectToolDrawingLine(sceneComponentType) {
  return {
    type: SELECT_TOOL_DRAWING_LINE,
    sceneComponentType,
  };
}

export function beginDrawingLine(layerID, x, y) {
  return {
    type: BEGIN_DRAWING_LINE,
    layerID,
    x,
    y,
  };
}

export function updateDrawingLine(x, y) {
  return {
    type: UPDATE_DRAWING_LINE,
    x,
    y,
  };
}

export function endDrawingLine(x, y) {
  return {
    type: END_DRAWING_LINE,
    x,
    y,
  };
}

export function increaseWidthSelectedWalls() {
  return {
    type: INCREASE_WIDTH_SELECTED_WALLS,
  };
}

export function decreaseWidthSelectedWalls() {
  return {
    type: DECREASE_WIDTH_SELECTED_WALLS,
  };
}

export function changeReferenceLine() {
  return {
    type: CHANGE_REFERENCE_LINE,
  };
}

export function changeLineType(lineId, lineType) {
  return {
    type: CHANGE_LINE_TYPE,
    lineId,
    lineType,
  };
}

export function changeLinesType(lineIds, lineType) {
  return {
    type: CHANGE_LINES_TYPE,
    lineIds,
    lineType,
  };
}
