import userEvent from '@testing-library/user-event';
import { screen } from '@testing-library/react';
import { serverMocks } from '../tests/utils/';
import { setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
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
    props = { ...props, ...changedProps };
    return renderReactPlanner(props, store);
  };

  it('Clicking on "Help" hide/shows help info', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    // Shows help
    userEvent.click(container.querySelector(`[tooltip="Help"]`));
    expect(screen.getByTestId('help-modal')).toBeInTheDocument();

    // Hide help
    userEvent.click(container.querySelector(`[tooltip="Help"]`));
    expect(screen.queryByTestId('help-modal')).not.toBeInTheDocument();
  });

  it('Clicking on "Copy & Paste" toggles copy paste info', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    // Shows info
    userEvent.click(container.querySelector(`[tooltip="Copy & paste tool"]`));
    expect(screen.getByTestId('copy-paste-panel')).toBeInTheDocument();

    // Hide info
    userEvent.click(container.querySelector(`[tooltip="Copy & paste tool"]`));
    expect(screen.queryByTestId('copy-paste-panel')).not.toBeInTheDocument();
  });
});
