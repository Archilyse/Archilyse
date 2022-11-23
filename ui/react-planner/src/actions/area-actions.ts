import { SELECT_AREA, UNSELECT_AREA } from '../constants';

export function selectArea(layerID, areaID) {
  return {
    type: SELECT_AREA,
    layerID,
    areaID,
  };
}

export function unselectArea(layerID, areaID) {
  return {
    type: UNSELECT_AREA,
    layerID,
    areaID,
  };
}
