import { PrototypesEnum } from '../constants';

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
