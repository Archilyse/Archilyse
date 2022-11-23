import userEvent from '@testing-library/user-event';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { serverMocks } from '../tests/utils/';
import { ITEM_DIRECTION, KEYBOARD_KEYS } from '../constants';
import {
  hoverAnArea,
  MockItemPositionValid,
  selectFromCatalog,
  setupMocks,
  setupRedux,
  setupServer,
  waitForSceneLoad,
} from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

describe('Items interaction', () => {
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

  it('Can change the direction of stairs', async () => {
    renderComponent();
    await waitForSceneLoad();

    const stairs = screen.getByTestId('item-stairs');
    expect(stairs).toBeInTheDocument();

    // Switch the direction to "Down"
    const itemElement = stairs.closest('g [data-element-root]');
    userEvent.click(itemElement);
    await waitFor(() => expect(itemElement).toHaveAttribute('data-selected', 'true'));

    // Check default direction
    expect(screen.getByText('Up')).toBeInTheDocument();

    userEvent.selectOptions(screen.getByLabelText('direction'), [ITEM_DIRECTION.DOWN]);

    // Label should be changed
    expect(screen.getByText('Down')).toBeInTheDocument();
  });

  it('Can modify length measures of an element using keyboard shortcuts', async () => {
    MockItemPositionValid(true);

    renderComponent();
    await waitForSceneLoad();

    const STAIRS_ORIGINAL_WIDTH = '49.000594519717346';
    const STAIRS_ORIGINAL_LENGTH = '299.0035671183041';

    const stairs = screen.getByTestId('item-stairs-rect');
    expect(stairs).toBeInTheDocument();

    // Check original length measures
    const stairsRect = screen.getByTestId('item-stairs-rect');
    expect(stairsRect).toHaveAttribute('width', STAIRS_ORIGINAL_WIDTH);
    expect(stairsRect).toHaveAttribute('height', STAIRS_ORIGINAL_LENGTH);

    const itemElement = stairs.closest('g [data-element-root]');
    userEvent.click(itemElement);
    await waitFor(() => expect(itemElement).toHaveAttribute('data-selected', 'true'));

    // Trigger CTRL + ArrowRight event (Increase Width)
    fireEvent.keyDown(stairs, { key: KEYBOARD_KEYS.ARROW_RIGHT, ctrlKey: true });
    expect(stairsRect).not.toHaveAttribute('width', STAIRS_ORIGINAL_WIDTH);

    // Trigger CTRL + ArrowUp event (Increase Length)
    fireEvent.keyDown(stairs, { key: KEYBOARD_KEYS.ARROW_UP, ctrlKey: true });
    expect(stairsRect).not.toHaveAttribute('height', STAIRS_ORIGINAL_LENGTH);

    // Trigger CTRL + ArrowLeft event (Decrease Width)
    fireEvent.keyDown(stairs, { key: KEYBOARD_KEYS.ARROW_LEFT, ctrlKey: true });
    expect(stairsRect).toHaveAttribute('width', STAIRS_ORIGINAL_WIDTH);

    // Trigger CTRL + ArrowDown event (Decrease Length)
    fireEvent.keyDown(stairs, { key: KEYBOARD_KEYS.ARROW_DOWN, ctrlKey: true });
    expect(stairsRect).toHaveAttribute('height', STAIRS_ORIGINAL_LENGTH);
  });

  it('Item can be changed while drawing', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    await selectFromCatalog(container, 'Shower');
    hoverAnArea();

    let shower = screen.queryByTestId('item-shower');
    expect(shower).toBeInTheDocument();

    await selectFromCatalog(container, 'Elevator');
    hoverAnArea();

    const elevator = screen.queryByTestId('item-elevator');
    expect(elevator).toBeInTheDocument();

    shower = screen.queryByTestId('item-shower');
    expect(shower).not.toBeInTheDocument();
  });
});
