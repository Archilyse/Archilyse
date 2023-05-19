import { OPENING_TYPE, PrototypesEnum } from '../constants';
import { OpeningType } from '../types';

export function getSelectedLayer(scene) {
  const layerID = scene.selectedLayer;
  return scene.layers[layerID];
}

export function getSelected(scene, prototype: typeof PrototypesEnum[keyof typeof PrototypesEnum]) {
  const layer = getSelectedLayer(scene);
  const selected = layer.selected[prototype];
  if (selected.length === 0) {
    return null;
  }
  return layer[prototype][selected[0]];
}

// @TODO: Perhaps move this to a different file like `catalog-utils` ?
export function doorHasWings(holeType: OpeningType) {
  return holeType === OPENING_TYPE.DOOR || holeType === OPENING_TYPE.ENTRANCE_DOOR;
}
