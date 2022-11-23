import { SeparatorsType } from '../constants';

const isScaling = state => {
  const selectedElement = state.drawingSupport.type;
  const scaleToolSelected = selectedElement === SeparatorsType.SCALE_TOOL;
  return scaleToolSelected;
};

export default isScaling;
