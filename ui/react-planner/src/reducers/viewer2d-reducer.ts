import {
  MODE_2D_PAN,
  MODE_2D_ZOOM_IN,
  MODE_2D_ZOOM_OUT,
  SELECT_TOOL_PAN,
  SELECT_TOOL_ZOOM_IN,
  SELECT_TOOL_ZOOM_OUT,
  UPDATE_2D_CAMERA,
} from '../constants';

export default (state, action) => {
  switch (action.type) {
    case UPDATE_2D_CAMERA:
      state.viewer2D = action.value;
      return state;

    case SELECT_TOOL_PAN:
      state.mode = MODE_2D_PAN;
      return state;

    case SELECT_TOOL_ZOOM_IN:
      state.mode = MODE_2D_ZOOM_IN;
      return state;

    case SELECT_TOOL_ZOOM_OUT:
      state.mode = MODE_2D_ZOOM_OUT;
      return state;
  }
};
