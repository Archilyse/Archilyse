import userEvent from '@testing-library/user-event';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { serverMocks } from '../tests/utils/';
import { KEYBOARD_KEYS } from '../constants';
import { setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

describe('Holes interaction', () => {
  let props;
  let store;

  beforeAll(() => {
    setupServer(server);
  });

  beforeEach(() => {
    const setup = setupRedux();
    props = setup.props;
    store = setup.store;
  });

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps, store };
    return renderReactPlanner(props, store);
  };

  it('Can modify length measures of a hole element using keyboard shortcuts', async () => {
    renderComponent();
    await waitForSceneLoad();

    const WINDOW_ORIGINAL_COORDS =
      '696.0793850347433, 914.5836326102403,696.0793850892591, 1144.5863674009402,718.0796466779346, 1144.5863673957256,718.0796466234189, 914.5836326050257';

    const WINDOW_EXPECTED_COORDS =
      '696.0793850341507, 912.0836028842544,696.0793850898516, 1147.086397126926,718.0796466785272, 1147.0863971217116,718.0796466228263, 912.0836028790399';

    // console.log(`all holes`,store.getState()['react-planner'].scene.layers['layer-1'].holes)

    const windows = screen.getAllByTestId('hole-window-polygon');
    const window = windows[0];
    expect(window).toBeInTheDocument();

    // Check original length measures
    expect(window).toHaveAttribute('points', WINDOW_ORIGINAL_COORDS);

    const itemElement = window.closest('g [data-element-root]');
    userEvent.click(itemElement);
    await waitFor(() => expect(itemElement).toHaveAttribute('data-selected', 'true'));

    // Trigger CTRL + ArrowRight event (Increase Width)
    fireEvent.keyDown(window, { key: KEYBOARD_KEYS.ARROW_RIGHT, ctrlKey: true });
    expect(window).toHaveAttribute('points', WINDOW_EXPECTED_COORDS);

    // Trigger CTRL + ArrowLeft event (Decrease Width)
    fireEvent.keyDown(window, { key: KEYBOARD_KEYS.ARROW_LEFT, ctrlKey: true });
    expect(window).toHaveAttribute('points', WINDOW_ORIGINAL_COORDS);
  });

  it('Can modify length measures of a hole element width adjustments in the sidebar', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    const WINDOW_ORIGINAL_COORDS =
      '696.0793850347433, 914.5836326102403,696.0793850892591, 1144.5863674009402,718.0796466779346, 1144.5863673957256,718.0796466234189, 914.5836326050257';

    const WINDOW_EXPECTED_COORDS =
      '696.0793850341507, 912.0836028842544,696.0793850898516, 1147.086397126926,718.0796466785272, 1147.0863971217116,718.0796466228263, 912.0836028790399';

    const windows = screen.getAllByTestId('hole-window-polygon');
    const window = windows[0];
    expect(window).toBeInTheDocument();

    // Check original length measures
    expect(window).toHaveAttribute('points', WINDOW_ORIGINAL_COORDS);

    const itemElement = window.closest('g [data-element-root]');
    userEvent.click(itemElement);
    await waitFor(() => expect(itemElement).toHaveAttribute('data-selected', 'true'));

    // Click on the arrow-up in the sidebar (Increase Width)
    const increaseWidthBtn = container.querySelector('#incr-length');
    fireEvent.click(increaseWidthBtn);
    expect(window).toHaveAttribute('points', WINDOW_EXPECTED_COORDS);

    // Click on the arrow-down in the sidebar (Decrease Width)
    const decreaseWidthBtn = container.querySelector('#decr-length');
    fireEvent.click(decreaseWidthBtn);
    expect(window).toHaveAttribute('points', WINDOW_ORIGINAL_COORDS);
  });

  it('Can modify sweeping points using shortcuts', async () => {
    renderComponent();
    await waitForSceneLoad();

    const SWEEPING_POINTS_ORIGINAL_PATH =
      'M998.7435243844454,856.8905477124367  A80.00095123154775,80.00095123154775 0 0,0 1078.7444756159932,936.8914989439845 L1078.7444756159932,856.8905477124367 L998.7435243844454,856.8905477124367 Z';

    const SWEEPING_POINTS_UPDATED_PATH =
      'M998.7435243844454,856.8905477124367  A80.00095123154775,80.00095123154775 0 0,1 1078.7444756159932,776.8895964808889 L1078.7444756159932,856.8905477124367 L998.7435243844454,856.8905477124367 Z';

    const allSweepingPoints = screen.getAllByTestId(/door-sweeping-points-/);
    const [sweepingPoints] = allSweepingPoints;
    expect(sweepingPoints).toHaveAttribute('d', SWEEPING_POINTS_ORIGINAL_PATH);

    // Select the door
    const holeElement = sweepingPoints.closest('g [data-element-root]');
    userEvent.click(holeElement);
    await waitFor(() => expect(holeElement).toHaveAttribute('data-selected', 'true'));

    // Trigger R (rotate/flip door)
    fireEvent.keyDown(holeElement, { key: KEYBOARD_KEYS.R });
    expect(sweepingPoints).toHaveAttribute('d', SWEEPING_POINTS_UPDATED_PATH);
  });

  it('Can modify sweeping points using the sidebar checkboxes', async () => {
    renderComponent();
    await waitForSceneLoad();

    const SWEEPING_POINTS_ORIGINAL_PATH =
      'M998.7435243844454,856.8905477124367  A80.00095123154775,80.00095123154775 0 0,0 1078.7444756159932,936.8914989439845 L1078.7444756159932,856.8905477124367 L998.7435243844454,856.8905477124367 Z';

    const SWEEPING_POINTS_FLIP_HORIZONTAL =
      'M998.7435243844454,856.8905477124367  A80.00095123154775,80.00095123154775 0 0,1 1078.7444756159932,776.8895964808889 L1078.7444756159932,856.8905477124367 L998.7435243844454,856.8905477124367 Z';

    const SWEEPING_POINTS_FLIP_VERTICAL =
      'M1078.7444756159932,856.8905477124367  A80.00095123154775,80.00095123154775 0 0,1 998.7435243844454,936.8914989439845 L998.7435243844454,856.8905477124367 L1078.7444756159932,856.8905477124367 Z';

    const allSweepingPoints = screen.getAllByTestId(/door-sweeping-points-/);
    const [sweepingPoint] = allSweepingPoints;
    expect(sweepingPoint).toHaveAttribute('d', SWEEPING_POINTS_ORIGINAL_PATH);

    // Select the door
    const holeElement = sweepingPoint.closest('g [data-element-root]');
    userEvent.click(holeElement);
    await waitFor(() => expect(holeElement).toHaveAttribute('data-selected', 'true'));

    // Flip horizontal
    const flipHorizontalCheckbox = screen.getByLabelText(/flip horizontal/i);
    userEvent.click(flipHorizontalCheckbox);
    expect(sweepingPoint).toHaveAttribute('d', SWEEPING_POINTS_FLIP_HORIZONTAL);

    // Flip horizontal
    const flipVerticalCheckbox = screen.getByLabelText(/flip vertical/i);
    userEvent.click(flipVerticalCheckbox);
    expect(sweepingPoint).toHaveAttribute('d', SWEEPING_POINTS_FLIP_VERTICAL);
  });

  it('limits the growth of hole length to the width of the parent line', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    const holeID = 'hole-91256661-d320-4625-ada5-c67afc9aa216';
    const hole = screen.getByTestId(holeID);
    expect(hole).toBeInTheDocument();

    userEvent.click(hole);
    await waitFor(() => expect(hole).toHaveAttribute('data-selected', 'true'));

    const originalHoleLength = screen.getByTestId('length-value-display');
    expect(originalHoleLength.getAttribute('value')).toBe('75 cm');

    // top out the length of the hole to meet the border of parent line
    const increaseWidthBtn = container.querySelector('#incr-length');
    fireEvent.click(increaseWidthBtn);

    const holePolygonElement = hole.lastElementChild.lastElementChild;

    const topOutLength = screen.getByTestId('length-value-display');
    const topOutCoordinates = holePolygonElement.getAttribute('points');
    expect(topOutLength.getAttribute('value')).toBe('80 cm');

    // simulate repeated attempts to increase hole length
    for (let i = 0; i < 10; i++) {
      fireEvent.click(increaseWidthBtn);
    }

    // after topping out max allowed length, user is not able to increase it
    const updatedHoleLength = screen.getByTestId('length-value-display');
    const updatedHoleCoordinates = holePolygonElement.getAttribute('points');
    expect(updatedHoleLength.getAttribute('value')).toBe(topOutLength.getAttribute('value'));
    expect(updatedHoleCoordinates).toStrictEqual(topOutCoordinates);
  });
});
