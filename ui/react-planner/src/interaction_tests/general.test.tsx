import { screen, waitFor } from '@testing-library/react';
import { MOCK_ANNOTATIONS_RESPONSE, MOCK_SITE_STRUCTURE, serverMocks } from '../tests/utils/';
import {
  INITIAL_BACKGROUND_HEIGHT,
  INITIAL_BACKGROUND_WIDTH,
  INITIAL_SCENE_HEIGHT,
  INITIAL_SCENE_WIDTH,
} from '../constants';
import { buildHandler, ENDPOINTS_PATTERN } from '../tests/utils/server-mocks';
import { Background } from '../types';
import { cloneDeep } from '../utils/export';
import {
  assertBackgroundDimensions,
  assertSceneDimensions,
  EXPECTED_SCENE_HEIGTH,
  EXPECTED_SCENE_WIDTH,
  expectSnackbarWithMessage,
  setupMocks,
  setupRedux,
  setupServer,
} from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

// @TODO: Erase it once scale/rotate button toolbar is visible for anyone
jest.mock('archilyse-ui-components', () => {
  /* eslint-disable */
  const React = require('react');
  const C = require('../constants');
  /* eslint-enable */

  return {
    // @ts-ignore
    ...jest.requireActual('archilyse-ui-components'),
    getUserRoles: () => [C.ROLES.ADMIN],
  };
});

describe('General flow on launching the editor', () => {
  let props;
  let store;

  beforeEach(() => {
    setupServer(server);

    const setup = setupRedux();
    props = setup.props;
    store = setup.store;
  });

  afterEach(() => {
    server.resetHandlers();
    jest.clearAllMocks();
  });

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    return renderReactPlanner(props, store);
  };

  it('On a not existing a plan: Shows an error', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', {}, 404));

    renderComponent();

    await expectSnackbarWithMessage('Could not find a plan for id');
  });

  it('On a general error fetching the plan: Shows an error', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', { msg: 'msg: Boom!' }, 500));

    renderComponent();

    await expectSnackbarWithMessage('Error fetching annotations');
  });

  it('On a new empty plan (master plan): Loads background image, adjust scene and ask user for scale', async () => {
    const mockSiteStructure = { ...MOCK_SITE_STRUCTURE, enforce_masterplan: true };
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', {}, 200),
        buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', { site_id: 1, is_masterplan: true }, 200),
        buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', mockSiteStructure, 200),
      ]
    );

    renderComponent();

    await assertBackgroundDimensions(INITIAL_BACKGROUND_WIDTH, INITIAL_BACKGROUND_HEIGHT);
    await assertSceneDimensions(INITIAL_SCENE_WIDTH, INITIAL_SCENE_HEIGHT);
    await expectSnackbarWithMessage('Plan without scale');
  });

  it('On a new empty plan (not master plan): Loads background image, adjust scene and asks user to import the annotation', async () => {
    const mockSiteStructure = { ...MOCK_SITE_STRUCTURE, enforce_masterplan: true };
    server.use(
      ...[
        buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', {}, 200),
        buildHandler(ENDPOINTS_PATTERN.PLAN_BY_ID, 'get', { site_id: 1, is_masterplan: false }, 200),
        buildHandler(ENDPOINTS_PATTERN.SITE_STRUCTURE, 'get', mockSiteStructure, 200),
      ]
    );

    renderComponent();

    await assertBackgroundDimensions(INITIAL_BACKGROUND_WIDTH, INITIAL_BACKGROUND_HEIGHT);
    await assertSceneDimensions(INITIAL_SCENE_WIDTH, INITIAL_SCENE_HEIGHT);
    await expectSnackbarWithMessage('Please import annotations');
  });

  it('On an existent plan: Loads background image, adjust scene, loads annotations & plan info', async () => {
    // Default setup (`setupServer`), no need to call server.use
    renderComponent();

    await assertBackgroundDimensions(EXPECTED_SCENE_WIDTH, EXPECTED_SCENE_HEIGTH);
    await assertSceneDimensions(EXPECTED_SCENE_WIDTH, EXPECTED_SCENE_HEIGTH);

    // Annotations are loaded
    await waitFor(() => expect(screen.getAllByTestId(/viewer-line-/).length).toBeGreaterThan(0), { timeout: 3000 });
    // Plan info is loaded with a panel and the "default heights"
    await waitFor(() => expect(screen.getAllByText(/Default heights/).length).toBeGreaterThan(0), {
      timeout: 3000,
    });
  });

  it('On an existent plan with modified background: Loads background image, adjust scene, loads annotations & plan info but used modified background data', async () => {
    const MODIFIED_BACKGROUND: Background = { width: 1581, height: 782, shift: { x: 750, y: 750 }, rotation: 0 };
    const MODIFIED_RESPONSE = cloneDeep(MOCK_ANNOTATIONS_RESPONSE);
    MODIFIED_RESPONSE.data.background = MODIFIED_BACKGROUND;
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', MODIFIED_RESPONSE, 200));

    renderComponent();

    // Scene initialized as usual
    await assertSceneDimensions(EXPECTED_SCENE_WIDTH, EXPECTED_SCENE_HEIGTH);

    // Annotations are loaded
    await waitFor(() => expect(screen.getAllByTestId(/viewer-line-/).length).toBeGreaterThan(0), { timeout: 3000 });
    // Plan info is loaded with a panel and the "default heights"
    await waitFor(() => expect(screen.getAllByText(/Default heights/).length).toBeGreaterThan(0), {
      timeout: 3000,
    });

    // Background will use the saved dimensions from the scene
    await assertBackgroundDimensions(MODIFIED_BACKGROUND.width, MODIFIED_BACKGROUND.height);
  });
});
