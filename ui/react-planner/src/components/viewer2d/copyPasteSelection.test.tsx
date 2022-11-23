import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createStore } from 'redux';
import { Models as PlannerModels, reducer as PlannerReducer } from '../../export'; //react-planner
import CopyPasteSelection from './copyPasteSelection';

const MOCK_SELECTION = {
  startPosition: { x: 10, y: 10 },
  endPosition: { x: 50, y: 50 },
};

const AppState = {
  'react-planner': new PlannerModels.State(),
};

const reducer = (state, action) => {
  state = state || AppState;
  state = PlannerReducer(state['react-planner'], action);
  state = {
    'react-planner': {
      ...state,
    },
  };
  return state;
};

describe('<CopyPasteSelection /> component', () => {
  let store;
  const renderComponent = (changedProps = {}) => {
    store = createStore(reducer, changedProps);
    return render(
      <Provider store={store}>
        <CopyPasteSelection />
      </Provider>
    );
  };

  it('With no starting or ending position, renders nothing', () => {
    const { container } = renderComponent();
    expect(container.firstChild).toBe(null);
  });

  const EXPECTED_X = 10;
  const EXPECTED_Y = 10;
  const EXPECTED_WIDTH = 40;
  const EXPECTED_HEIGHT = 40;

  it('While drawing renders a rectangle with solid border', () => {
    const changedState = {
      'react-planner': { copyPaste: { selection: MOCK_SELECTION, drawing: true } },
    };
    renderComponent(changedState);
    const copyPasteSelection = screen.getByTestId('copy-paste-selection');
    const copyPasteSelectionRect = copyPasteSelection.querySelector('rect');
    expect(copyPasteSelection).toBeInTheDocument();

    // Assert correct dimensions
    expect(copyPasteSelection).toHaveAttribute(
      'transform',
      `translate(${EXPECTED_X}, ${EXPECTED_Y}) rotate(0, ${EXPECTED_WIDTH / 2}, ${EXPECTED_HEIGHT / 2})`
    );
    expect(copyPasteSelectionRect).toHaveAttribute('width', `${EXPECTED_WIDTH}`);
    expect(copyPasteSelectionRect).toHaveAttribute('height', `${EXPECTED_HEIGHT}`);

    // Assert correct border
    expect(copyPasteSelectionRect).toHaveAttribute('class', '');
    expect(copyPasteSelectionRect).toHaveAttribute('stroke-dasharray', 'none');
  });

  it('After finishing drawing renders a rectangle with a dash border and with grab cursor', () => {
    const changedState = {
      'react-planner': { copyPaste: { selection: MOCK_SELECTION, drawing: false } },
    };
    renderComponent(changedState);

    const copyPasteSelection = screen.getByTestId('copy-paste-selection');
    const copyPasteSelectionRect = copyPasteSelection.querySelector('rect');
    expect(copyPasteSelection).toBeInTheDocument();

    // Assert correct dimensions
    expect(copyPasteSelection).toHaveAttribute(
      'transform',
      `translate(${EXPECTED_X}, ${EXPECTED_Y}) rotate(0, ${EXPECTED_WIDTH / 2}, ${EXPECTED_HEIGHT / 2})`
    );
    expect(copyPasteSelectionRect).toHaveAttribute('width', `${EXPECTED_WIDTH}`);
    expect(copyPasteSelectionRect).toHaveAttribute('height', `${EXPECTED_HEIGHT}`);

    // Assert correct border
    expect(copyPasteSelectionRect).toHaveAttribute('class', 'selectionComplete');
    expect(copyPasteSelectionRect).toHaveAttribute('stroke-dasharray', '10,10');
  });

  it('While drawing the selection, the rotation anchor is not rendered', () => {
    const changedState = {
      'react-planner': { copyPaste: { selection: MOCK_SELECTION, drawing: true } },
    };
    renderComponent(changedState);

    const rotationAnchor = screen.queryByTestId('copy-paste-rotation-anchor');
    expect(rotationAnchor).not.toBeInTheDocument();
  });

  it('After the selection is made, the rotation anchor is correctly rendered', () => {
    const changedState = {
      'react-planner': { copyPaste: { selection: MOCK_SELECTION, drawing: false } },
    };
    renderComponent(changedState);

    const rotationAnchor = screen.queryByTestId('copy-paste-rotation-anchor');
    expect(rotationAnchor).toBeInTheDocument();

    const EXPECTED_ORIENTATION_POINT_CX = '20';
    const EXPECTED_ORIENTATION_POINT_CY = '48.2842712474619';
    const EXPECTED_ROTATION_CIRCLE_CX = '20';
    const EXPECTED_ROTATION_CIRCLE_CY = '20';
    const EXPECTED_ROTATION_CIRCLE_R = '28.284271247461902';

    const [orientationPoint, rotationCircle] = rotationAnchor.querySelectorAll('circle') as any;

    expect(orientationPoint).toBeInTheDocument();
    expect(orientationPoint).toHaveAttribute('cx', EXPECTED_ORIENTATION_POINT_CX);
    expect(orientationPoint).toHaveAttribute('cy', EXPECTED_ORIENTATION_POINT_CY);

    expect(rotationCircle).toBeInTheDocument();
    expect(rotationCircle).toHaveAttribute('cx', EXPECTED_ROTATION_CIRCLE_CX);
    expect(rotationCircle).toHaveAttribute('cy', EXPECTED_ROTATION_CIRCLE_CY);
    expect(rotationCircle).toHaveAttribute('r', EXPECTED_ROTATION_CIRCLE_R);
  });
});
