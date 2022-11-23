import { SELECT_LAYER } from '../constants';

export function selectLayer(layerID) {
  return {
    type: SELECT_LAYER,
    layerID,
  };
}
