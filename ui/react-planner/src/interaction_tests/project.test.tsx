import { fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MOCK_ANNOTATIONS_RESPONSE, serverMocks } from '../tests/utils/';
import { KEYBOARD_KEYS, MODE_ROTATE_SCALE_BACKGROUND } from '../constants';
import { buildHandler, ENDPOINTS_PATTERN } from '../tests/utils/server-mocks';
import {
  assertBackgroundDimensions,
  assertBackgroundPosition,
  assertBackgroundTransform,
  clicksOnAnArea,
  expectSnackbarWithMessage,
  selectFromCatalog,
  setupMocks,
  setupRedux,
  setupServer,
  waitForSceneLoad,
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
    ...jest.requireActual('archilyse-ui-components'),
    getUserRoles: () => [C.ROLES.ADMIN],
  };
});

// https://stackoverflow.com/a/60669731/2904072
// Cannot use EXPECTED_SCENE_* variables here as they seem to create a conflict (cyclic?) with the imports.
jest.mock('../utils/get-img-dimensions.ts', () => {
  return {
    __esModule: true,
    default: jest
      .fn()
      .mockResolvedValue({ width: 2187, height: 1640, originalImgElem: { src: '', width: 2187, height: 1640 } }),
    namedExport: jest
      .fn()
      .mockResolvedValue({ width: 2187, height: 1640, originalImgElem: { src: '', width: 2187, height: 1640 } }),
  };
});

describe('Project interaction', () => {
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
  });

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps, store };
    return renderReactPlanner(props, store);
  };

  it('Renders correctly, loads floorplan img and adjust scene to its dimensions', async () => {
    renderComponent();
    await waitForSceneLoad();
  });

  it('Can be saved if there are changes (no API validation)', async () => {
    // @TODO: Ask for validated plan after adjusting the pattern regexp
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN_NOT_VALIDATED, 'put', MOCK_ANNOTATIONS_RESPONSE, 200));

    const { container } = renderComponent();
    await waitForSceneLoad();

    // Perform a change
    await selectFromCatalog(container, 'Kitchen');
    clicksOnAnArea();

    // Exit drawing mode to be able to save
    userEvent.click(container.querySelector(`[tooltip="Select tool"]`));

    userEvent.click(container.querySelector(`[tooltip="Save project"]`));
    const notificationSuccess = await screen.findByText(/Project saved$/);
    expect(notificationSuccess).toBeInTheDocument();
  });

  it('Can not be saved again if there are no changes to save', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN_NOT_VALIDATED, 'put', MOCK_ANNOTATIONS_RESPONSE, 200));

    const { container } = renderComponent();
    await waitForSceneLoad();

    expect(container.querySelector(`[tooltip="Save project"]`)).not.toBeInTheDocument();

    // Save tooltip is different and clicking on it does nothing
    userEvent.click(container.querySelector(`[tooltip="Project saved"]`));
    const notificationSuccess = await screen.queryByText(/Project saved$/);
    expect(notificationSuccess).not.toBeInTheDocument();
  });

  it('An operation is undone pressing ctrl+z', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    // Select the stairs we want to remove
    const stairs = screen.getByTestId('item-stairs');
    userEvent.click(stairs);
    expect(stairs).toBeInTheDocument();

    // Pressing delete, removes the stairs from the screen
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.DELETE, ctrlKey: true });
    expect(stairs).not.toBeInTheDocument();

    // Pressing ctrl+z once brings back the stairs
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.Z, ctrlKey: true });
    expect(screen.getByTestId('item-stairs')).toBeInTheDocument();
  });

  it('A plan is saved by pressing ctrl+S', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    // Select the stairs to be able to save
    const stairs = screen.getByTestId('item-stairs');
    userEvent.click(stairs);
    expect(stairs).toBeInTheDocument();

    // Pressing ctrl+S saves the project
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.S, ctrlKey: true });
    await expectSnackbarWithMessage('Project saved');
  });

  it('If there are no operations after loading the scene, pressing ctrl+z does nothing', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    const initialLinesNumber = screen.getAllByTestId(/viewer-line-/).length;

    // Scene remains unchanged after ctrl +z (see https://github.com/Archilyse/slam/pull/2981)
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.Z, ctrlKey: true });
    const linesAfterUndo = screen.getAllByTestId(/viewer-line-/);
    expect(initialLinesNumber).toBe(linesAfterUndo.length);
  });

  it(`The width & height of the floorplan can be changed in ${MODE_ROTATE_SCALE_BACKGROUND} using the background scale input in the sidebar`, async () => {
    const INITIAL_WIDTH = 2187;
    const INITIAL_HEIGHT = 1640;
    const NEW_BACKGROUND_SCALE = 0.96;

    const { container } = renderComponent();
    await waitForSceneLoad();

    await assertBackgroundDimensions(INITIAL_WIDTH, INITIAL_HEIGHT);

    // Switch to rotate/scale background mode
    userEvent.click(container.querySelector(`[tooltip="Rotate/scale background"]`));

    // Change the scale
    const scaleInput = await screen.findByLabelText(/Scale/);
    fireEvent.change(scaleInput, { target: { value: NEW_BACKGROUND_SCALE } });

    // Floorplan should have been resized accordingly
    const EXPECTED_WIDTH = Math.floor(INITIAL_WIDTH * NEW_BACKGROUND_SCALE);
    const EXPECTED_HEIGHT = Math.floor(INITIAL_HEIGHT * NEW_BACKGROUND_SCALE);
    await assertBackgroundDimensions(EXPECTED_WIDTH, EXPECTED_HEIGHT);
  });

  it(`The scene zoom level can be reset by clicking the Fit to scale button`, async () => {
    const INITIAL_VALUE = 1.198;
    const CHANGED_VALUE = 1.2;

    const { container } = renderComponent();
    await waitForSceneLoad();

    // Get initial zoom level value
    let zoomValue = screen.queryByText(`Zoom: ${INITIAL_VALUE.toFixed(3)}X`);
    expect(zoomValue).toBeInTheDocument();

    // Scroll within the plan
    const floorPlan = screen.getByTestId('floorplan-img');
    await fireEvent.wheel(floorPlan);

    // Ascertain that the zoom level value has changed
    zoomValue = screen.queryByText(`Zoom: ${CHANGED_VALUE.toFixed(3)}X`);
    expect(zoomValue).toBeInTheDocument();

    // Clicking the 'Fit to screen' button resets the zoom level
    userEvent.click(container.querySelector(`[tooltip="Fit to screen"]`));

    // Ascertain that the zoom value is reset to the initial value
    await waitForSceneLoad();
    zoomValue = screen.queryByText(`Zoom: ${INITIAL_VALUE.toFixed(3)}X`);
    expect(zoomValue).toBeInTheDocument();
  });

  it(`The rotation of the floorplan can be changed in ${MODE_ROTATE_SCALE_BACKGROUND} using the sidebar`, async () => {
    const INITIAL_WIDTH = 2187;
    const INITIAL_HEIGHT = 1640;
    const INITIAL_ROTATION = 0;
    const NEW_ROTATION = 45;

    const { container } = renderComponent();
    await waitForSceneLoad();

    const initialTransform = `rotate(${INITIAL_ROTATION}, ${INITIAL_WIDTH / 2}, ${INITIAL_HEIGHT / 2})`;
    await assertBackgroundTransform(initialTransform);

    // Switch to rotate/scale background mode
    userEvent.click(container.querySelector(`[tooltip="Rotate/scale background"]`));

    // Change rotation
    const widthInput = screen.getByLabelText(/rotation/i);
    fireEvent.change(widthInput, { target: { value: NEW_ROTATION } });

    const expectedTransform = `rotate(${NEW_ROTATION}, ${INITIAL_WIDTH / 2}, ${INITIAL_HEIGHT / 2})`;
    await assertBackgroundTransform(expectedTransform);
  });

  it(`The position of the floorplan can be changed in ${MODE_ROTATE_SCALE_BACKGROUND} using the sidebar`, async () => {
    const INITIAL_X = 0;
    const INITIAL_Y = 0;

    const NEW_SHIFT_X = 10;
    const NEW_SHIFT_Y = 20;

    const EXPECTED_NEW_X = 10;
    const EXPECTED_NEW_Y = 20 * -1; // As the Y in the planner is "inverted" and starts bottom left

    const { container } = renderComponent();
    await waitForSceneLoad();

    await assertBackgroundPosition(INITIAL_X, INITIAL_Y);

    // Switch to rotate/scale background mode
    userEvent.click(container.querySelector(`[tooltip="Rotate/scale background"]`));

    // Shift X and Y
    const shiftX = screen.getByLabelText(/Shift X/i);
    fireEvent.change(shiftX, { target: { value: NEW_SHIFT_X } });

    const shiftY = screen.getByLabelText(/Shift Y/i);
    fireEvent.change(shiftY, { target: { value: NEW_SHIFT_Y } });

    // The background position should have changed
    await assertBackgroundPosition(EXPECTED_NEW_X, EXPECTED_NEW_Y);
  });

  it('Snackbar displays the API error message when saving the project', async () => {
    server.use(
      buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN_NOT_VALIDATED, 'put', { msg: 'Simulations are running' }, 400)
    );

    const { container } = renderComponent();
    await waitForSceneLoad();

    // Perform a change
    await selectFromCatalog(container, 'Kitchen');
    clicksOnAnArea();

    // Exit drawing mode to be able to save
    userEvent.click(container.querySelector(`[tooltip="Select tool"]`));

    userEvent.click(container.querySelector(`[tooltip="Save project"]`));
    const notificationFailure = await screen.findByText(
      /Error occured while saving a project: Simulations are running/
    );
    expect(notificationFailure).toBeInTheDocument();
  });

  it('Shows a message while the project is being saved', async () => {
    const delayResponse = 7000; // To simulate a long response and force the snackbar to be shown for a while
    server.use(
      buildHandler(
        ENDPOINTS_PATTERN.ANNOTATION_PLAN_NOT_VALIDATED,
        'put',
        MOCK_ANNOTATIONS_RESPONSE,
        200,
        delayResponse
      )
    );

    const { container } = renderComponent();
    await waitForSceneLoad();

    // Perform a change
    await selectFromCatalog(container, 'Kitchen');
    clicksOnAnArea();

    // Exit drawing mode to be able to save
    userEvent.click(container.querySelector(`[tooltip="Select tool"]`));

    // Save and expect a snackbar
    userEvent.click(container.querySelector(`[tooltip="Save project"]`));
    const savingMessage = await screen.findByText(/Saving/);
    expect(savingMessage).toBeInTheDocument();
  });
});
