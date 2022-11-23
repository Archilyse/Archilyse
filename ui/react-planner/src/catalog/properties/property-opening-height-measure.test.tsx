import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { Models as PlannerModels } from '../../export'; //react-planner
import { OPENING_NAME } from '../../constants';
import { getMockState } from '../../tests/utils/tests-utils';
import { MOCK_STATE } from '../../tests/utils';
import { OpeningHeightsInputForm } from './export';

const AppState = {
  'react-planner': new PlannerModels.State(),
};

describe('User Input behaviour tests', () => {
  let store;
  const mockStore = configureStore();
  const mockedState = {
    ...MOCK_STATE,
    planInfo: {
      default_wall_height: 2.8,
      default_door_height: 2.2,
      default_window_lower_edge: 0.8,
      default_window_upper_edge: 2.0,
    },
  };
  const state = getMockState(mockedState);

  const renderComponent = props => {
    return render(
      <Provider store={store}>
        <OpeningHeightsInputForm {...props} />
      </Provider>
    );
  };

  beforeEach(() => {
    store = mockStore(AppState);
  });

  afterEach(() => {
    store.clearActions();
  });

  const configs = { label: 'heights' };
  it.each([
    [OPENING_NAME.DOOR, '20', '180', true],
    [OPENING_NAME.DOOR, '-20', '180', false],
    [OPENING_NAME.DOOR, '20', '290', false],
    [OPENING_NAME.DOOR, '180', '20', false],
    [OPENING_NAME.ENTRANCE_DOOR, '20', '180', true],
    [OPENING_NAME.ENTRANCE_DOOR, '-20', '180', false],
    [OPENING_NAME.ENTRANCE_DOOR, '20', '290', false],
    [OPENING_NAME.ENTRANCE_DOOR, '180', '20', false],
    [OPENING_NAME.SLIDING_DOOR, '20', '180', true],
    [OPENING_NAME.SLIDING_DOOR, '-20', '180', false],
    [OPENING_NAME.SLIDING_DOOR, '20', '290', false],
    [OPENING_NAME.SLIDING_DOOR, '180', '20', false],
    [OPENING_NAME.WINDOW, '80', '220', true],
    [OPENING_NAME.SLIDING_DOOR, '-80', '220', false],
    [OPENING_NAME.SLIDING_DOOR, '80', '290', false],
    [OPENING_NAME.SLIDING_DOOR, '220', '80', false],
  ])('User Input tests', (openingName, inputLowerEdge, inputUpperEdge, expectValid) => {
    const mockCallback = jest.fn(newLength => null);
    const value = { lower_edge: null, upper_edge: null };
    const sourceElement = { name: openingName };
    const props = {
      value: value,
      configs: configs,
      state: state,
      sourceElement: sourceElement,
      onUpdate: mockCallback,
    };
    renderComponent(props);
    const is_window = openingName == OPENING_NAME.WINDOW ? true : false;
    const defaultValueLowerEdge = is_window ? '80' : '0';
    const defaultValueUpperEdge = is_window ? '200' : '220';
    const lowerEdgeInputField = screen.getByDisplayValue(defaultValueLowerEdge);
    const uperEdgeInputField = screen.getByDisplayValue(defaultValueUpperEdge);
    const button = screen.getByRole('button');

    userEvent.clear(lowerEdgeInputField);
    userEvent.type(lowerEdgeInputField, inputLowerEdge);
    userEvent.clear(uperEdgeInputField);
    userEvent.type(uperEdgeInputField, inputUpperEdge);
    userEvent.click(button);

    if (expectValid) {
      expect(mockCallback.mock.calls.length).toBe(1);
      expect(mockCallback.mock.calls[0][0].lower_edge).toBe(Number(inputLowerEdge));
      expect(mockCallback.mock.calls[0][0].upper_edge).toBe(Number(inputUpperEdge));
      expect(screen.getByDisplayValue(inputLowerEdge)).toBeInTheDocument();
      expect(screen.getByDisplayValue(inputLowerEdge)).toBeInTheDocument();
    } else {
      expect(mockCallback.mock.calls.length).toBe(0);
      expect(screen.getByDisplayValue(defaultValueLowerEdge)).toBeInTheDocument();
      expect(screen.getByDisplayValue(defaultValueUpperEdge)).toBeInTheDocument();
    }
  });
});
