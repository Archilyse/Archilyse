import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { MOCK_STATE } from '../../tests/utils';
import { getMockState } from '../../tests/utils/tests-utils';
import { PREDICTION_FEEDBACK_EVENTS, SHOW_SNACKBAR, TOGGLE_AUTOLABELLING_FEEDBACK } from '../../constants';
import { ProviderMetrics } from '../../providers';
import PanelAutoLabellingFeedback from './panel-auto-labelling-feedback';

describe('PanelAutoLabellingFeedback', () => {
  let store;
  const mockStore = configureStore();

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        {/* @ts-ignore */}
        <PanelAutoLabellingFeedback />
      </Provider>
    );
  };

  beforeEach(() => {
    const state = { 'react-planner': getMockState({ ...MOCK_STATE }) };
    store = mockStore(state);
  });

  afterEach(() => {
    store.clearActions();
  });

  it('Renders with two icons: Thumbs up & Thumbs down', () => {
    renderComponent();
    expect(screen.getByTestId('thumbs-up')).toBeInTheDocument();
    expect(screen.getByTestId('thumbs-down')).toBeInTheDocument();
  });

  it('Clicking on thumbs up: Registers the feedback, shows a snackbar and closes the panel', () => {
    renderComponent();
    const providerMetricsMock = jest.spyOn(ProviderMetrics, 'trackPredictionFeedback');

    userEvent.click(screen.getByTestId('thumbs-up'));

    expect(providerMetricsMock).toBeCalledWith(PREDICTION_FEEDBACK_EVENTS.PREDICTION_GOOD);

    const actions = store.getActions();
    expect(actions[0].type).toBe(SHOW_SNACKBAR);
    expect(actions[1].type).toBe(TOGGLE_AUTOLABELLING_FEEDBACK);
  });

  it('Clicking on thumbs down: Registers the feedback, shows a snackbar and closes the panel', () => {
    renderComponent();
    const providerMetricsMock = jest.spyOn(ProviderMetrics, 'trackPredictionFeedback');

    userEvent.click(screen.getByTestId('thumbs-down'));

    expect(providerMetricsMock).toBeCalledWith(PREDICTION_FEEDBACK_EVENTS.PREDICTION_BAD);

    const actions = store.getActions();
    expect(actions[0].type).toBe(SHOW_SNACKBAR);
    expect(actions[1].type).toBe(TOGGLE_AUTOLABELLING_FEEDBACK);
  });
});
