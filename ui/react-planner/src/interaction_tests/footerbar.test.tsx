import userEvent from '@testing-library/user-event';
import { fireEvent, screen } from '@testing-library/react';
import { serverMocks } from '../tests/utils/';
import { KEYBOARD_KEYS } from '../constants';
import {
  clicksOnAnArea,
  selectFromCatalog,
  setupMocks,
  setupRedux,
  setupServer,
  VIEWER_REGEXP,
  waitForSceneLoad,
} from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

describe('Toolbar interaction', () => {
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

  it('Clicking on "Show snap" hide/shows snapping elements to the user while drawing', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    // Start drawing
    await selectFromCatalog(container, 'Wall');
    clicksOnAnArea();

    // Snaps are shown
    let snapsVisible = screen.queryAllByTestId('snap-element').length > 0;
    expect(snapsVisible).toBeTruthy();

    // Exit drawing mode
    const viewer = screen.getByTestId(VIEWER_REGEXP);
    fireEvent.keyDown(viewer, { key: KEYBOARD_KEYS.ESCAPE });

    // Toggle button
    const footerBarButton = screen.getByText(/Show snap/);
    expect(footerBarButton).toBeInTheDocument();
    userEvent.click(footerBarButton);

    // Snaps elements are no longer visible
    await selectFromCatalog(container, 'Wall');
    clicksOnAnArea();

    snapsVisible = screen.queryAllByTestId('snap-element').length > 0;
    expect(snapsVisible).toBeFalsy();
  });
});
