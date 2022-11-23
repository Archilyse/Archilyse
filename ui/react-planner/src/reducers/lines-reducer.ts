import { Line } from '../class/export';
import { history } from '../utils/export';
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

export default (state, action) => {
  switch (action.type) {
    case SELECT_TOOL_DRAWING_LINE:
      return Line.selectToolDrawingLine(state, action.sceneComponentType).updatedState;

    case BEGIN_DRAWING_LINE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Line.beginDrawingLine(state, action.layerID, action.x, action.y).updatedState;

    case UPDATE_DRAWING_LINE:
      return Line.updateDrawingLine(state, action.x, action.y).updatedState;

    case END_DRAWING_LINE:
      return Line.endDrawingLine(state, action.x, action.y).updatedState;

    case SELECT_LINE:
      return Line.select(state, action.layerID, action.lineID).updatedState;

    case UNSELECT_LINE:
      return Line.unselect(state, action.layerID, action.lineID).updatedState;

    case INCREASE_WIDTH_SELECTED_WALLS:
      return Line.updateWidthSelectedWalls(state, 1).updatedState;

    case DECREASE_WIDTH_SELECTED_WALLS:
      return Line.updateWidthSelectedWalls(state, -1).updatedState;

    case CHANGE_REFERENCE_LINE:
      return Line.changeReferenceLine(state).updatedState;
    case CHANGE_LINE_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Line.changeLineType(state, action.lineId, action.lineType).updatedState;

    case CHANGE_LINES_TYPE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Line.changeLinesType(state, action.lineIds, action.lineType).updatedState;

    default:
      return state;
  }
};
