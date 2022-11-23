import React from 'react';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import {
  CLEAR_SCALE_DRAWING,
  PAGE_SIZES,
  REQUEST_STATUS_BY_ACTION,
  RESCALE_NOT_ALLOWED_MESSAGE,
  SAVE_PROJECT_PENDING,
  SCALING_REQUIRED_MEASUREMENT_COUNT,
  SET_PLAN_SCALE,
} from '../../../constants';
import { Models as PlannerModels } from '../../../export'; //react-planner
import { getCleanMockState, getMockState } from '../../../tests/utils/tests-utils';
import { MOCK_AREA } from '../../../tests/utils';
import PanelScale from './panel-scale';
import * as utils from './utils';

const AppState = {
  'react-planner': new PlannerModels.State(),
};

const MOCK_SCALE_TOOL = {
  distance: 0,
  areaSize: 0,
  userHasChangedMeasures: false,
};

const MOCK_LINE_POINTS = [
  [0, 50],
  [50, 50],
];

const MOCK_POLYGON_POINTS = [
  { x: 308.98, y: 371.14 },
  { x: 557.63, y: 552.15 },
  { x: 560.71, y: 545.31 },
  { x: 661.85, y: 319.95 },
  { x: 313.31, y: 365.21 },
  { x: 661.85, y: 319.95 },
];

const MOCK_PAPER_FORMAT = Object.keys(PAGE_SIZES)[1];
const MOCK_SCALE_RATIO = '50';

const DEFAULT_STATE = {
  scaleTool: MOCK_SCALE_TOOL,
  floorScales: [],
  scene: getCleanMockState().scene, // Need a clean one because otherwise we cannot scale
  requesStatus: { [REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES]: {} },
};

jest.mock('react-router-dom', () => ({
  // @ts-ignore
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn().mockReturnValue({ id: '1' }),
}));

describe('Panel scale component', () => {
  let props;
  let store;

  const mockStore = configureStore([thunk]);
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return render(
      <Provider store={store}>
        <PanelScale {...props} />
      </Provider>
    );
  };

  beforeEach(() => {
    const newAppState = {
      'react-planner': {
        ...AppState['react-planner'],
        scaleValidated: true,
      },
    };
    store = mockStore(newAppState);
  });

  afterEach(() => {
    store.clearActions();
    jest.restoreAllMocks();
  });

  const getMockStore = newState => {
    const props = {
      state: {
        ...newState,
        scene: {
          ...DEFAULT_STATE.scene,
          ...newState?.scene,
        },
        scaleTool: { distance: null },
        floorScales: DEFAULT_STATE.floorScales,
        requestStatus: DEFAULT_STATE.requesStatus,
      },
    };

    const newAppState = {
      'react-planner': {
        ...AppState['react-planner'],
        ...props.state,
      },
    };

    return mockStore(newAppState);
  };

  it('Shows a text with instructions', () => {
    renderComponent();
    expect(screen.getByText(/Take \d measures or set page specs/)).toBeInTheDocument();
  });

  it('Triggers an action with the expected scale as payload using page specs', () => {
    const MOCK_PAPER_FORMAT = Object.keys(PAGE_SIZES)[1];
    const MOCK_SCALE_RATIO = '50';
    const EXPECTED_SCALE = 2.0797403357330295;

    const state = { scene: { ...DEFAULT_STATE.scene, paperFormat: MOCK_PAPER_FORMAT, scaleRatio: MOCK_SCALE_RATIO } };
    store = getMockStore(state);

    renderComponent(props);

    userEvent.click(screen.getByText(/Validate scale using format\/ratio/));

    const [firstAction, secondAction] = store.getActions();
    expect(firstAction.type).toBe(SET_PLAN_SCALE);
    expect(firstAction.payload).toBe(EXPECTED_SCALE);

    expect(secondAction.type).toBe(SAVE_PROJECT_PENDING);
  });

  it('Triggers an action with the expected scale as payload using measures', () => {
    jest.spyOn(utils, 'getPointsFromScaleToolLines').mockImplementation(() => MOCK_POLYGON_POINTS);

    const mockScaleArea = { ...MOCK_AREA, isScaleArea: true };

    // Fake measurements taken
    const measurementChange = jest.spyOn(React, 'useState');
    const fakeMeasurements = [
      {
        points: MOCK_POLYGON_POINTS,
        areaSize: 0.25,
        area: mockScaleArea,
      },
    ];
    measurementChange.mockImplementation(() => [fakeMeasurements, jest.fn()]);

    const state = { scaleTool: { distance: null } };
    store = getMockStore(state);

    renderComponent(props);

    const SAVE_BUTTON = screen.getByText('Save measure');
    userEvent.click(SAVE_BUTTON);

    const ACTIONS = store.getActions();

    const SAVE_PROJECT_PENDING_ACTION = ACTIONS.some(item => item.type === SAVE_PROJECT_PENDING);
    const SET_PLAN_SCALE_ACTION = ACTIONS.some(item => item.type === SET_PLAN_SCALE);

    expect(SAVE_PROJECT_PENDING_ACTION).toBeTruthy;
    expect(SET_PLAN_SCALE_ACTION).toBeTruthy;
  });

  it('Triggers an action with page specs expected scale when using both specs and measures', () => {
    jest.spyOn(utils, 'getPointsFromScaleToolLines').mockImplementation(() => MOCK_POLYGON_POINTS);

    const PAGE_SPECS_SCALE = 2.0797403357330295;
    const mockScaleArea = { ...MOCK_AREA, isScaleArea: true };

    // Fake measurements taken
    const measurementChange = jest.spyOn(React, 'useState');
    const measuresToTake = Array.from(Array(SCALING_REQUIRED_MEASUREMENT_COUNT).keys());
    const fakeMeasurements = measuresToTake.map(_ => ({
      points: MOCK_POLYGON_POINTS,
      areaSize: 0.25,
      area: mockScaleArea,
    }));
    measurementChange.mockImplementation(() => [fakeMeasurements, jest.fn()]);

    const state = {
      scene: { ...DEFAULT_STATE.scene, paperFormat: MOCK_PAPER_FORMAT, scaleRatio: MOCK_SCALE_RATIO },
      scaleTool: { distance: null },
    };
    store = getMockStore(state);

    renderComponent(props);

    // There will be a button to validate using format ratio only
    expect(screen.queryByText(/Validate scale$/)).not.toBeInTheDocument();

    userEvent.click(screen.getByText(/Validate scale using format\/ratio/));

    const [firstAction, secondAction] = store.getActions();
    expect(firstAction.type).toBe(SET_PLAN_SCALE);
    expect(firstAction.payload).toBe(PAGE_SPECS_SCALE);

    expect(secondAction.type).toBe(SAVE_PROJECT_PENDING);
  });

  it('Cannot rescale if the plan contains some annotations', () => {
    jest.spyOn(utils, 'getPointsFromScaleToolLines').mockImplementation(() => MOCK_LINE_POINTS);

    const INITIAL_DISTANCE = 0;
    const mockStateWithAnnotations = getMockState();

    const state = {
      scene: mockStateWithAnnotations.scene,
      scaleTool: { distance: INITIAL_DISTANCE },
    };
    store = getMockStore(state);

    renderComponent();

    expect(screen.queryByText(/Validate scale/)).not.toBeInTheDocument();
    const saveButton = screen.queryByText(new RegExp(RESCALE_NOT_ALLOWED_MESSAGE));
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });

  it('Triggers an action to clear the scale drawing when clicking on the `Clear button`', () => {
    const measurementChange = jest.spyOn(React, 'useState');
    measurementChange.mockImplementation(() => [[{ points: MOCK_POLYGON_POINTS, areaSize: 0.25 }], jest.fn()]);

    const state = getCleanMockState();
    state.requestStatus = DEFAULT_STATE.requesStatus;

    store = getMockStore(state);

    renderComponent();

    userEvent.click(screen.getByText(/Clear/));

    const [lastAction] = store.getActions();
    expect(lastAction.type).toBe(CLEAR_SCALE_DRAWING);
  });
});
