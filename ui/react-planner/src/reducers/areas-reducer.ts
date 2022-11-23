import { Area } from '../class/export';
import { SELECT_AREA, UNSELECT_AREA } from '../constants';

export default (state, action) => {
  switch (action.type) {
    case SELECT_AREA:
      return Area.select(state, action.layerID, action.areaID).updatedState;
    case UNSELECT_AREA:
      return Area.unselect(state, action.layerID, action.areaID).updatedState;
    default:
      return state;
  }
};
