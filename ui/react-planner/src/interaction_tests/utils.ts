import thunk from 'redux-thunk';
// Mock Annotations response contains almost the same data as in tests/fixtures/react_planner_annotations/plan_background_image.json
// that is loaded in db_fixtures_ui
import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { applyMiddleware, compose, createStore } from 'redux';
import configureStore from 'redux-mock-store';
import {
  MOCK_ANNOTATIONS_RESPONSE,
  MOCK_AUTHENTICATION,
  MOCK_PLAN_RESPONSE,
  MOCK_SITE_STRUCTURE,
  serverMocks,
} from '../tests/utils/';
import { Models as PlannerModels, Plugins as PlannerPlugins, reducer as PlannerReducer } from '../export'; //react-planner
import MyCatalog from '../catalog-elements/mycatalog';
import Item from '../class/item';
import cloneDeep from '../utils/clone-deep';

const { buildHandler, ENDPOINTS_PATTERN } = serverMocks;

export const VIEWER_REGEXP = /viewer-[0-9]+x[0-9]+/;
export const EXPECTED_SCENE_WIDTH = 2187;
export const EXPECTED_SCENE_HEIGTH = 1640;

export const selectFromCatalog = async (container, itemName) => {
  let catalogToolbar = screen.queryByTestId('catalog-toolbar');
  if (!catalogToolbar) {
    await waitFor(() => expect(container.querySelector(`[tooltip="Open catalog"]`)).toBeTruthy(), {
      timeout: 3000,
    });
    userEvent.click(container.querySelector(`[tooltip="Open catalog"]`));
    catalogToolbar = screen.queryByTestId('catalog-toolbar');
  }
  const [catalogElement] = await within(catalogToolbar).findAllByText(new RegExp(itemName));
  userEvent.click(catalogElement);
};

export const clicksOnAnArea = () => {
  const [firstArea] = screen.getAllByTestId(/viewer-area-/);
  userEvent.click(firstArea);
};

export const hoverAnArea = () => {
  const [firstArea] = screen.getAllByTestId(/viewer-area-/);
  userEvent.hover(firstArea);
};

export const clickAndDragAMainVertex = store => {
  const allLines = Object.values(store.getState()['react-planner'].scene.layers['layer-1'].lines) as any;
  const firstLine = allLines[0];
  const lineId = firstLine.id;
  const mainVertexId = firstLine.vertices[0];

  const lineIdElem = screen.getByTestId(`viewer-line-${lineId}`);
  userEvent.click(lineIdElem);

  const mainVertexElem = screen.getByTestId(`vertex-${mainVertexId}`);
  fireEvent.mouseDown(mainVertexElem);
  fireEvent.mouseMove(mainVertexElem);
  fireEvent.mouseUp(mainVertexElem);
};

export const getLineBySeparatorType = (separatorType): any => {
  const layer = MOCK_ANNOTATIONS_RESPONSE.data.layers['layer-1'];
  const line = Object.values(layer.lines).find(line => line.type === separatorType);
  return line;
};

export const MockItemPositionValid = isValid => {
  const itemSpy = jest.spyOn(Item, 'isSelectedItemInValidPosition');
  itemSpy.mockImplementation(() => {
    return isValid;
  });
};

export const expectSnackbarWithMessage = async message => {
  await waitFor(() => expect(screen.getByText(new RegExp(message, 'i'))).toBeInTheDocument(), {
    timeout: 3000,
  });
};

export const assertBackgroundDimensions = async (width, height) => {
  const floorplanImg = screen.getByTestId('floorplan-img');
  expect(floorplanImg).toBeInTheDocument();
  await waitFor(() => expect(floorplanImg).toHaveAttribute('width', String(width)), { timeout: 6000 });
  await waitFor(() => expect(floorplanImg).toHaveAttribute('height', String(height)), { timeout: 6000 });
};

export const assertBackgroundTransform = async expectedTransform => {
  const backgroundImage = screen.getByTestId('background-img-group');
  await waitFor(() => expect(backgroundImage).toHaveAttribute('transform', expectedTransform), { timeout: 6000 });
};

export const assertBackgroundPosition = async (expectedX: number, expectedY: number) => {
  const backgroundImage = screen.getByTestId('floorplan-img');
  await waitFor(() => expect(backgroundImage).toHaveAttribute('x', String(expectedX)), { timeout: 6000 });
  await waitFor(() => expect(backgroundImage).toHaveAttribute('y', String(expectedY)), { timeout: 6000 });
};

export const assertSceneDimensions = async (width, height) => {
  await waitFor(() => expect(screen.getByTestId(new RegExp(`viewer-${width}x${height}`))).toBeInTheDocument(), {
    timeout: 3000,
  });
};

export const waitForSceneLoad = async () => {
  await waitFor(() => expect(screen.getByTestId(VIEWER_REGEXP)).toBeInTheDocument(), { timeout: 6000 });
  const viewer = screen.getByTestId(VIEWER_REGEXP);
  await waitFor(() => expect(viewer).toHaveAttribute('class', 'floorplan-img-loaded centered'), { timeout: 6000 });
  await assertBackgroundDimensions(EXPECTED_SCENE_WIDTH, EXPECTED_SCENE_HEIGTH);
  await waitFor(() => expect(screen.queryAllByTestId(/viewer-line-/).length).toBeTruthy(), { timeout: 6000 });
};

export const setupServer = server => {
  server.listen();
  server.use(
    ...[
      buildHandler(ENDPOINTS_PATTERN.FLOORPLAN_IMG_PLAN, 'get', new Blob(), 200),
      buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', MOCK_ANNOTATIONS_RESPONSE, 200),
      buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', MOCK_PLAN_RESPONSE, 200),
      buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', MOCK_SITE_STRUCTURE),
    ]
  );
};

// @TODO: Rename to `setupHelpers` mocks (jest.mock()) cannot be placed here as inside of the body of a function they won't work.
export const setupMocks = () => {
  // helper to find the new sizes => console.log(screen.getByText((content, element) => content.endsWith('m²')));
  window.URL.createObjectURL = jest.fn(() => 'blob:http://localhost:9000/2b9be933-9b4f-4ec5-9d16-337423936ff9');
};

export const setupRedux = (withActionsHistory = false) => {
  MOCK_AUTHENTICATION();

  // Real state & reducer used in renderer.jsx
  const AppState = {
    'react-planner': new PlannerModels.State(),
  };

  const reducer = (state, action) => {
    state = state || cloneDeep(AppState);
    state = PlannerReducer(state['react-planner'], action);
    state = {
      'react-planner': state,
    };
    return state;
  };

  const plugins = [PlannerPlugins.Keyboard()];

  const props = {
    catalog: MyCatalog,
    width: 3000,
    height: 2000,
    plugins,
    stateExtractor: state => state['react-planner'],
  };

  const mockStore = configureStore([thunk]);
  const mockedStore = mockStore(AppState);

  const originalStore = createStore(reducer, null, compose(applyMiddleware(thunk)));
  let store = originalStore;

  // extend current store with other functions from 'redux-mock-store'
  // like `getActions()`
  if (withActionsHistory) {
    store = {
      ...mockedStore,
      ...originalStore,
    };
    const originalDispatch = originalStore.dispatch;
    store.dispatch = function (action) {
      mockedStore.dispatch(action);
      return originalDispatch(action);
    };
  }
  return { props, store };
};
