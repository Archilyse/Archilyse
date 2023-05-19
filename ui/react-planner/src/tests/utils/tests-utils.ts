import { State } from '../../models';
import { Hole as HoleType, State as StateType } from '../../types';
import { Hole, Item, Line } from '../../class/export';
import { OPENING_TYPE, SeparatorsType } from '../../constants';
import MyCatalog from '../../catalog-elements/mycatalog';
import { cloneDeep } from '../../utils/export';
import MOCK_STATE from './mockState';

export const SELECTED_LAYER_ID = MOCK_STATE.scene.selectedLayer;

export const getCleanMockState = () => {
  const clonedState = cloneDeep(MOCK_STATE);
  const defaultLayer = clonedState.scene.layers['layer-1'] as any;
  defaultLayer.vertices = {};
  defaultLayer.lines = {};

  return getMockState({
    ...clonedState,
    snapMask: {},
  });
};
// @TODO: Add type here and see everything implode
export const getMockState = (jsMock: any = MOCK_STATE): StateType =>
  cloneDeep(new State({ ...jsMock, catalog: MyCatalog }));

export const addLineToState = (
  state,
  lineType: typeof SeparatorsType[keyof typeof SeparatorsType],
  points: { x0: number; y0: number; x1: number; y1: number },
  additionalProperties = {},
  options = { createAuxVertices: true, forceVertexCreation: false }
) => {
  const { x0, y0, x1, y1 } = points;
  const LAYER_ID = state.scene.selectedLayer;
  const lineResult = Line.create(state, LAYER_ID, lineType, x0, y0, x1, y1, additionalProperties, options);
  const result = cloneDeep(lineResult);
  return { updatedState: result.updatedState, line: result.line };
};

export const addItemToState = (state, type: string, x: number, y: number, rotation = 0, additionalProperties = {}) => {
  const LAYER_ID = state.scene.selectedLayer;
  const itemResult = Item.create(state, LAYER_ID, type, x, y, rotation, additionalProperties);
  const result = cloneDeep(itemResult);
  return { updatedState: result.updatedState, item: result.item };
};

export const addHoleToState = (
  state,
  holeType: typeof OPENING_TYPE[keyof typeof OPENING_TYPE],
  lineID: string,
  coordinates: HoleType['coordinates'],
  sweepingPoints: HoleType['door_sweeping_points'] = null,
  additionalProperties = {}
) => {
  const LAYER_ID = state.scene.selectedLayer;
  const holeResult = Hole.create(state, LAYER_ID, holeType, lineID, coordinates, sweepingPoints, additionalProperties);
  const result = cloneDeep(holeResult);
  return { updatedState: result.updatedState, hole: result.hole };
};
