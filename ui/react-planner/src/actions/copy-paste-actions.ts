import {
  BEGIN_COPY_PASTE_SELECTION,
  BEGIN_DRAGGING_COPY_PASTE_SELECTION,
  BEGIN_ROTATING_COPY_PASTE_SELECTION,
  END_COPY_PASTE_SELECTION,
  END_DRAGGING_COPY_PASTE_SELECTION,
  END_ROTATING_COPY_PASTE_SELECTION,
  RESTORE_COPY_PASTE_FROM_ANOTHER_PLAN,
  SAVE_COPY_PASTE_SELECTION,
  UPDATE_COPY_PASTE_SELECTION,
  UPDATE_DRAGGING_COPY_PASTE_SELECTION,
  UPDATE_ROTATING_COPY_PASTE_SELECTION,
} from '../constants';

export function beginCopyPasteSelection(x, y) {
  return {
    type: BEGIN_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function updateCopyPasteSelection(x, y) {
  return {
    type: UPDATE_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function endCopyPasteSelection(x, y) {
  return {
    type: END_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function beginDraggingCopyPasteSelection(x, y) {
  return {
    type: BEGIN_DRAGGING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function updateDraggingCopyPasteSelection(x, y) {
  return {
    type: UPDATE_DRAGGING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function endDraggingCopyPasteSelection(x, y) {
  return {
    type: END_DRAGGING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function restoreCopyPasteFromAnotherPlan() {
  return {
    type: RESTORE_COPY_PASTE_FROM_ANOTHER_PLAN,
  };
}

export function saveCopyPasteSelection() {
  return {
    type: SAVE_COPY_PASTE_SELECTION,
  };
}

export function beginRotatingCopyPasteSelection(x, y) {
  return {
    type: BEGIN_ROTATING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function updateRotatingCopyPasteSelection(x, y) {
  return {
    type: UPDATE_ROTATING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}

export function endRotatingCopyPasteSelection(x, y) {
  return {
    type: END_ROTATING_COPY_PASTE_SELECTION,
    payload: { x, y },
  };
}
