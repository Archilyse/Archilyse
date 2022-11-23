import {
  BEGIN_DRAGGING_HOLE,
  CHANGE_HOLE_TYPE,
  CHANGE_HOLES_TYPE,
  COPY_SELECTED_HOLE,
  DECREASE_WIDTH_SELECTED_HOLES,
  END_DRAGGING_HOLE,
  END_DRAWING_HOLE,
  INCREASE_WIDTH_SELECTED_HOLES,
  ROTATE_SELECTED_DOORS,
  SELECT_HOLE,
  SELECT_TOOL_DRAWING_HOLE,
  UNSELECT_HOLE,
  UPDATE_DRAGGING_HOLE,
  UPDATE_DRAWING_HOLE,
} from '../constants';

export function selectHole(layerID, holeID) {
  return {
    type: SELECT_HOLE,
    layerID,
    holeID,
  };
}

export function unselectHole(layerID, holeID) {
  return {
    type: UNSELECT_HOLE,
    layerID,
    holeID,
  };
}

export function selectToolDrawingHole(sceneComponentType) {
  return {
    type: SELECT_TOOL_DRAWING_HOLE,
    sceneComponentType,
  };
}

export function updateDrawingHole(layerID, x, y) {
  return {
    type: UPDATE_DRAWING_HOLE,
    layerID,
    x,
    y,
  };
}

export function endDrawingHole(layerID, x, y) {
  return {
    type: END_DRAWING_HOLE,
    layerID,
    x,
    y,
  };
}

export function beginDraggingHole(layerID, holeID, x, y) {
  return {
    type: BEGIN_DRAGGING_HOLE,
    layerID,
    holeID,
    x,
    y,
  };
}

export function updateDraggingHole(x, y) {
  return {
    type: UPDATE_DRAGGING_HOLE,
    x,
    y,
  };
}

export function endDraggingHole(x, y) {
  return {
    type: END_DRAGGING_HOLE,
    x,
    y,
  };
}

export function rotateSelectedDoors() {
  return {
    type: ROTATE_SELECTED_DOORS,
  };
}

export function increaseWidthSelectedHoles() {
  return {
    type: INCREASE_WIDTH_SELECTED_HOLES,
  };
}

export function decreaseWidthSelectedHoles() {
  return {
    type: DECREASE_WIDTH_SELECTED_HOLES,
  };
}

export function copySelectedHole() {
  return {
    type: COPY_SELECTED_HOLE,
  };
}

export function changeHoleType(holeId, holeType) {
  return {
    type: CHANGE_HOLE_TYPE,
    holeId,
    holeType,
  };
}

export function changeHolesType(holeIds, holeType) {
  return {
    type: CHANGE_HOLES_TYPE,
    holeIds,
    holeType,
  };
}
