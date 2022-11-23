import { Hole } from '../class/export';
import { history } from '../utils/export';
import {
  BEGIN_DRAGGING_HOLE,
  CHANGE_HOLE_TYPE,
  CHANGE_HOLES_TYPE,
  COPY_SELECTED_HOLE,
  DECREASE_WIDTH_SELECTED_HOLES,
  END_DRAGGING_HOLE,
  END_DRAWING_HOLE,
  INCREASE_WIDTH_SELECTED_HOLES,
  MEASURE_STEP_HOLE,
  ROTATE_SELECTED_DOORS,
  SELECT_HOLE,
  SELECT_TOOL_DRAWING_HOLE,
  UNSELECT_HOLE,
  UPDATE_DRAGGING_HOLE,
  UPDATE_DRAWING_HOLE,
} from '../constants';

export default (state, action) => {
  switch (action.type) {
    case SELECT_TOOL_DRAWING_HOLE:
      return Hole.selectToolDrawingHole(state, action.sceneComponentType).updatedState;

    case UPDATE_DRAWING_HOLE:
      return Hole.updateDrawingHole(state, action.layerID, action.x, action.y).updatedState;

    case END_DRAWING_HOLE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.endDrawingHole(state, action.layerID, action.x, action.y).updatedState;

    case BEGIN_DRAGGING_HOLE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.beginDraggingHole(state, action.layerID, action.holeID, action.x, action.y).updatedState;

    case UPDATE_DRAGGING_HOLE:
      return Hole.updateDraggingHole(state, action.x, action.y).updatedState;

    case END_DRAGGING_HOLE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.endDraggingHole(state, action.x, action.y).updatedState;

    case SELECT_HOLE:
      return Hole.select(state, action.layerID, action.holeID).updatedState;

    case UNSELECT_HOLE:
      return Hole.unselect(state, action.layerID, action.holeID).updatedState;

    case ROTATE_SELECTED_DOORS:
      return Hole.rotateSelectedDoors(state).updatedState;

    case INCREASE_WIDTH_SELECTED_HOLES:
      return Hole.updateLengthMeasuresSelectedHoles(state, MEASURE_STEP_HOLE).updatedState;

    case DECREASE_WIDTH_SELECTED_HOLES:
      return Hole.updateLengthMeasuresSelectedHoles(state, -MEASURE_STEP_HOLE).updatedState;

    case COPY_SELECTED_HOLE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.copySelectedHole(state).updatedState;

    case CHANGE_HOLE_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.changeHoleType(state, action.holeId, action.holeType).updatedState;

    case CHANGE_HOLES_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Hole.changeHolesType(state, action.holeIds, action.holeType).updatedState;

    default:
      return state;
  }
};
