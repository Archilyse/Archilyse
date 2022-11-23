import { RectangleSelectTool } from '../class/export';
import { BEGIN_RECTANGLE_SELECTION, END_RECTANGLE_SELECTION, UPDATE_RECTANGLE_SELECTION } from '../constants';

export default (state, action) => {
  switch (action.type) {
    case BEGIN_RECTANGLE_SELECTION:
      return RectangleSelectTool.beginRectangleSelection(state, action).updatedState;
    case UPDATE_RECTANGLE_SELECTION:
      return RectangleSelectTool.updateRectangleSelection(state, action).updatedState;
    case END_RECTANGLE_SELECTION:
      return RectangleSelectTool.endRectangleSelection(state, action).updatedState;

    default:
      return state;
  }
};
