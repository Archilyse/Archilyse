import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { serverMocks } from '../tests/utils/';
import { setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

describe('Areas interaction', () => {
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
    props = { ...props, ...changedProps };
    return renderReactPlanner(props, store);
  };

  it('Clicking an area selects it', async () => {
    renderComponent();
    await waitForSceneLoad();

    const [firstArea] = screen.getAllByTestId(/viewer-area-/);
    userEvent.click(firstArea);

    // The area has been selected
    expect(firstArea).toHaveAttribute('data-selected', 'true');
  });

  it('Changing width of the wall of an area affects the size of the area', async () => {
    const EXPECTED_ORIGINAL_SIZE = /^16.91/;
    const EXPECTED_SIZE_AFTER_WIDTH_CHANGE = /^16.48/;

    renderComponent();
    await waitForSceneLoad();

    // Original size is there
    expect(screen.getByText(EXPECTED_ORIGINAL_SIZE)).toBeInTheDocument();
    const lineId = 'viewer-line-6639705d-b391-4318-a00b-6742d193f3be';
    const line = screen.getByTestId(lineId);

    // Select line and decrease width
    userEvent.click(line);
    userEvent.selectOptions(screen.getByLabelText('width'), ['40']);

    // The original size won't be on the screen
    expect(screen.getByText(EXPECTED_SIZE_AFTER_WIDTH_CHANGE)).toBeInTheDocument();
    expect(screen.queryByText(EXPECTED_ORIGINAL_SIZE)).not.toBeInTheDocument();
  });
});
