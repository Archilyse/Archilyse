/* Simplified version of the current store */
import { MODE_IDLE } from '../../constants';
import { Scene, State } from '../../types';
import scene from './mockSimpleScene.json';

const MOCK_STATE: Partial<State> = {
  availableAreaTypes: [],
  floorplanImgUrl: '',
  floorplanDimensions: { width: null, height: null },
  mode: MODE_IDLE,
  scaleTool: {
    distance: 0,
    areaSize: 0,
    userHasChangedMeasures: false,
  },
  scene: (scene as unknown) as Scene,
  viewer2D: {},
  errors: [],
  warnings: [],
  zoom: 1,
  snapMask: {},
  scaleValidated: true,
  requestStatus: {
    GET_PLAN_ANNOTATIONS: {
      status: 'REJECTED',
      error: {},
    },
  },
  highlightedError: '',
  validationErrors: [],
};

export default MOCK_STATE;
