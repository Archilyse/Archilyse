import { SeparatorsType } from '../constants';

export default state => {
  const selectedLayer = state.scene.selectedLayer;
  const layer = state.scene.layers[selectedLayer];
  const lines = Object.values(layer.lines);
  const linesDrawn = lines.filter((line: any) => line.type !== SeparatorsType.SCALE_TOOL).length > 0;
  const items = Object.values(layer.items);
  const itemsDrawn = items.length > 0;
  const holes = Object.values(layer.holes);
  const holesDrawn = holes.length > 0;

  return linesDrawn || itemsDrawn || holesDrawn;
};
