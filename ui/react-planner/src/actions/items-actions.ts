import {
  BEGIN_DRAGGING_ITEM,
  BEGIN_ROTATING_ITEM,
  CHANGE_ITEM_TYPE,
  CHANGE_ITEMS_TYPE,
  COPY_SELECTED_ITEM,
  DECREASE_LENGTH_SELECTED_ITEMS,
  DECREASE_WIDTH_SELECTED_ITEMS,
  END_DRAGGING_ITEM,
  END_DRAWING_ITEM,
  END_ROTATING_ITEM,
  INCREASE_LENGTH_SELECTED_ITEMS,
  INCREASE_WIDTH_SELECTED_ITEMS,
  SELECT_ITEM,
  SELECT_TOOL_DRAWING_ITEM,
  UNSELECT_ITEM,
  UPDATE_DRAGGING_ITEM,
  UPDATE_DRAWING_ITEM,
  UPDATE_ROTATING_ITEM,
} from '../constants';

export function selectItem(layerID, itemID) {
  return {
    type: SELECT_ITEM,
    layerID,
    itemID,
  };
}

export function unselectItem(layerID, itemID) {
  return {
    type: UNSELECT_ITEM,
    layerID,
    itemID,
  };
}

export function selectToolDrawingItem(sceneComponentType) {
  return {
    type: SELECT_TOOL_DRAWING_ITEM,
    sceneComponentType,
  };
}

export function updateDrawingItem(layerID, x, y) {
  return {
    type: UPDATE_DRAWING_ITEM,
    layerID,
    x,
    y,
  };
}

export function endDrawingItem(layerID, x, y) {
  return {
    type: END_DRAWING_ITEM,
    layerID,
    x,
    y,
  };
}

export function beginDraggingItem(layerID, itemID, x, y) {
  return {
    type: BEGIN_DRAGGING_ITEM,
    layerID,
    itemID,
    x,
    y,
  };
}

export function updateDraggingItem(x, y) {
  return {
    type: UPDATE_DRAGGING_ITEM,
    x,
    y,
  };
}

export function endDraggingItem(x, y) {
  return {
    type: END_DRAGGING_ITEM,
    x,
    y,
  };
}

export function beginRotatingItem(layerID, itemID, x, y) {
  return {
    type: BEGIN_ROTATING_ITEM,
    layerID,
    itemID,
    x,
    y,
  };
}

export function updateRotatingItem(x, y) {
  return {
    type: UPDATE_ROTATING_ITEM,
    x,
    y,
  };
}

export function endRotatingItem(x, y) {
  return {
    type: END_ROTATING_ITEM,
    x,
    y,
  };
}

export function increaseWidthSelectedItems() {
  return {
    type: INCREASE_WIDTH_SELECTED_ITEMS,
  };
}

export function decreaseWidthSelectedItems() {
  return {
    type: DECREASE_WIDTH_SELECTED_ITEMS,
  };
}

export function increaseLengthSelectedItems() {
  return {
    type: INCREASE_LENGTH_SELECTED_ITEMS,
  };
}

export function decreaseLengthSelectedItems() {
  return {
    type: DECREASE_LENGTH_SELECTED_ITEMS,
  };
}

export function copySelectedItem() {
  return {
    type: COPY_SELECTED_ITEM,
  };
}

export function changeItemType(itemId, itemType) {
  return {
    type: CHANGE_ITEM_TYPE,
    itemId,
    itemType,
  };
}

export function changeItemsType(itemIds, itemType) {
  return {
    type: CHANGE_ITEMS_TYPE,
    itemIds,
    itemType,
  };
}