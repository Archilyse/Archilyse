import { Item } from '../class/export';
import { history } from '../utils/export';
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
  MEASURE_STEP_ITEM,
  SELECT_ITEM,
  SELECT_TOOL_DRAWING_ITEM,
  UNSELECT_ITEM,
  UPDATE_DRAGGING_ITEM,
  UPDATE_DRAWING_ITEM,
  UPDATE_ROTATING_ITEM,
} from '../constants';

export default (state, action) => {
  switch (action.type) {
    case SELECT_ITEM:
      return Item.select(state, action.layerID, action.itemID).updatedState;

    case UNSELECT_ITEM:
      return Item.unselect(state, action.layerID, action.itemID).updatedState;

    case SELECT_TOOL_DRAWING_ITEM:
      return Item.selectToolDrawingItem(state, action.sceneComponentType).updatedState;

    case UPDATE_DRAWING_ITEM:
      return Item.updateDrawingItem(state, action.layerID, action.x, action.y).updatedState;

    case END_DRAWING_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.endDrawingItem(state, action.layerID, action.x, action.y).updatedState;

    case BEGIN_DRAGGING_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.beginDraggingItem(state, action.layerID, action.itemID, action.x, action.y).updatedState;

    case UPDATE_DRAGGING_ITEM:
      return Item.updateDraggingItem(state, action.x, action.y).updatedState;

    case END_DRAGGING_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.endDraggingItem(state, action.x, action.y).updatedState;

    case BEGIN_ROTATING_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.beginRotatingItem(state, action.layerID, action.itemID, action.x, action.y).updatedState;

    case UPDATE_ROTATING_ITEM:
      return Item.updateRotatingItem(state, action.x, action.y).updatedState;

    case END_ROTATING_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.endRotatingItem(state, action.x, action.y).updatedState;

    case INCREASE_WIDTH_SELECTED_ITEMS:
      return Item.updateLengthMeasuresSelectedItems(state, { width: MEASURE_STEP_ITEM }).updatedState;

    case DECREASE_WIDTH_SELECTED_ITEMS:
      return Item.updateLengthMeasuresSelectedItems(state, { width: -MEASURE_STEP_ITEM }).updatedState;

    case INCREASE_LENGTH_SELECTED_ITEMS:
      return Item.updateLengthMeasuresSelectedItems(state, { length: MEASURE_STEP_ITEM }).updatedState;

    case DECREASE_LENGTH_SELECTED_ITEMS:
      return Item.updateLengthMeasuresSelectedItems(state, { length: -MEASURE_STEP_ITEM }).updatedState;

    case COPY_SELECTED_ITEM:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.copySelectedItem(state).updatedState;

    case CHANGE_ITEM_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.changeItemType(state, action.itemId, action.itemType).updatedState;

    case CHANGE_ITEMS_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Item.changeItemsType(state, action.itemIds, action.itemType).updatedState;

    default:
      return state;
  }
};
