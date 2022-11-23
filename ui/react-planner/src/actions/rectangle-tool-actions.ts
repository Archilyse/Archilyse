import { BEGIN_RECTANGLE_SELECTION, END_RECTANGLE_SELECTION, UPDATE_RECTANGLE_SELECTION } from '../constants';

export function beginRectangleSelection(x, y) {
  return {
    type: BEGIN_RECTANGLE_SELECTION,
    payload: { x, y },
  };
}

export function updateRectangleSelection(x, y) {
  return {
    type: UPDATE_RECTANGLE_SELECTION,
    payload: { x, y },
  };
}

export function endRectangleSelection(x, y) {
  return {
    type: END_RECTANGLE_SELECTION,
    payload: { x, y },
  };
}
