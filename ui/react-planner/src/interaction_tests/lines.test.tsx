import { fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { serverMocks } from '../tests/utils/';
import { KEYBOARD_KEYS, POSSIBLE_WALL_WIDTHS, SeparatorsType } from '../constants';
import { getLineBySeparatorType, setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

const LINE_ID = 'viewer-line-6639705d-b391-4318-a00b-6742d193f3be';

describe('Lines interaction', () => {
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

  it.each([[SeparatorsType.WALL], [SeparatorsType.RAILING]])(
    'Pressing "+/-" change the width of a %s',
    async lineType => {
      const { container } = renderComponent();
      await waitForSceneLoad();

      // select a line by type to change it
      const line = getLineBySeparatorType(lineType);
      const lineElement = await screen.findByTestId(`viewer-line-${line.id}`);
      userEvent.click(lineElement);

      // Get current width
      const width = screen.getByLabelText('width') as HTMLSelectElement;
      const originalWidth = width.value;

      // Current width is not there after pressing '+'
      fireEvent.keyDown(container, { key: KEYBOARD_KEYS.PLUS });
      expect(screen.getByLabelText('width')).not.toHaveValue(originalWidth);

      // Pressing '-' will get back the original width
      fireEvent.keyDown(container, { key: KEYBOARD_KEYS.MINUS });
      expect(screen.getByLabelText('width')).toHaveValue(originalWidth);
    }
  );

  it.each([[SeparatorsType.WALL], [SeparatorsType.RAILING]])(
    'Pressing "f" on a selected %s, does not change the reference line',
    async lineType => {
      const { container } = renderComponent();
      await waitForSceneLoad();

      const line = getLineBySeparatorType(lineType);
      const referenceLine = line.properties.referenceLine;
      const lineElement = await screen.findByTestId(`viewer-line-${line.id}`);
      userEvent.click(lineElement);

      fireEvent.keyDown(container, { key: KEYBOARD_KEYS.F });
      const referenceLineText = screen.getByText(new RegExp(referenceLine)) as HTMLSelectElement;
      expect(referenceLineText).toBeInTheDocument();
    }
  );

  it('Should display only those wall widths for selection, that are allowed', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    const line = await screen.findByTestId(LINE_ID);
    userEvent.click(line);

    userEvent.click(container.querySelector('#width'));
    POSSIBLE_WALL_WIDTHS.forEach(t => {
      expect(`${t} cm`).toBeInTheDocument;
    });
  });

  it('Reverts to the original wall width after increasing it and undoing the action.', async () => {
    const { container } = renderComponent();
    await waitForSceneLoad();

    const line = await screen.findByTestId(LINE_ID);
    const originalLineCoordinates = line.children[0].getAttribute('points');

    userEvent.click(line);
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.PLUS });

    const updatedLineCoordinates = line.children[0].getAttribute('points');
    expect(originalLineCoordinates).not.toBe(updatedLineCoordinates);

    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.Z, ctrlKey: true });

    const revertedLineCoordinates = line.children[0].getAttribute('points');
    expect(originalLineCoordinates).toBe(revertedLineCoordinates);
  });
});
