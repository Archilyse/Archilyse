import * as React from 'react';
import userEvent from '@testing-library/user-event';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { MOCK_VALIDATION_ERRORS } from '../../tests/utils';
import { COLORS } from '../../constants';
import { Models as PlannerModels } from '../../export'; //react-planner
import PanelValidationErrors from './panel-validation-errors';

let AppState = {
  'react-planner': new PlannerModels.State(),
};

describe('Panel validation component', () => {
  let store;
  const mockStore = configureStore();
  const renderComponent = (changedProps = {}) => {
    return render(
      <Provider store={store}>
        {/* @ts-ignore */}
        <PanelValidationErrors />
      </Provider>
    );
  };

  beforeEach(() => {
    AppState = {
      'react-planner': {
        ...AppState['react-planner'],
        validationErrors: MOCK_VALIDATION_ERRORS,
        highlightedError: '',
      },
    };
    store = mockStore(AppState);
  });

  afterEach(() => {
    store.clearActions();
  });

  it('Renders correctly when there are no errors', () => {
    let newState = { errors: [], validationErrors: [] } as any;
    newState = {
      'react-planner': {
        ...AppState['react-planner'],
        ...newState,
      },
    };
    store = mockStore(newState);
    renderComponent();
    expect(screen.queryByTestId(/error-list/)).not.toBeInTheDocument();
  });

  it('Displays a set of blocking & non-blocking errors', () => {
    renderComponent();
    MOCK_VALIDATION_ERRORS.forEach((error, index) => {
      const errorNumber = index + 1;
      expect(screen.getAllByText(error.type)).toBeTruthy();
      expect(screen.getAllByText(error.text)).toBeTruthy();
      expect(screen.getByTestId(`error-list-${errorNumber}`)).toHaveStyle({
        color: error.is_blocking ? 'red' : 'yellow',
      });
    });
  });

  it('Show a highlighted error in a different color', () => {
    const MOCK_HIGHLIGHTED_ERROR = MOCK_VALIDATION_ERRORS[0].object_id;
    let newState = { highlightedError: MOCK_HIGHLIGHTED_ERROR } as any;

    newState = {
      'react-planner': {
        ...AppState['react-planner'],
        ...newState,
      },
    };
    store = mockStore(newState);
    renderComponent();

    MOCK_VALIDATION_ERRORS.forEach((error, index) => {
      const errorNumber = index + 1;
      const isHighlighted = error.object_id === MOCK_HIGHLIGHTED_ERROR;
      if (isHighlighted) {
        expect(screen.getByTestId(`error-list-${errorNumber}`)).toHaveStyle({
          color: COLORS.PRIMARY_COLOR,
        });
      } else {
        expect(screen.getByTestId(`error-list-${errorNumber}`)).not.toHaveStyle({
          color: COLORS.PRIMARY_COLOR,
        });
      }
    });
  });

  it('On hover over an error, an action is dispatched to highlight it', () => {
    renderComponent();
    const errorToHover = MOCK_VALIDATION_ERRORS[1];
    userEvent.hover(screen.getByText(errorToHover.text));
    const [action] = store.getActions();
    expect(action.payload).toBe(errorToHover.object_id);
  });
});
