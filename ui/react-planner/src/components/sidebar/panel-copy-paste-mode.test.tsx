import * as React from 'react';
import { ProviderStorage } from 'archilyse-ui-components';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createStore } from 'redux';
import { Models as PlannerModels, reducer as PlannerReducer } from '../../export'; //react-planner
import PanelCopyPasteMode from './panel-copy-paste-mode';

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

jest.mock('react-router-dom', () => ({
  // @ts-ignore
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn().mockReturnValue({ id: '36' }),
}));

describe('Panel copy paste', () => {
  let store;
  const renderComponent = (changedProps = {}) => {
    store = createStore(reducer, changedProps);
    return render(
      <Provider store={store}>
        {/* @ts-ignore */}
        <PanelCopyPasteMode />
      </Provider>
    );
  };

  it('Renders instructions on how the use copy paste in the same plan at the beginning', () => {
    renderComponent();
    expect(screen.queryByText(/To paste in a different plan/)).not.toBeInTheDocument();
  });

  it('Renders instructions to paste in the same and in another plan after drawing the selection', () => {
    const MOCK_SELECTION = {
      startPosition: { x: 304, y: 1157 },
      endPosition: { x: 466, y: 1013 },
      draggingPosition: { x: -1, y: -1 },
    };
    const MOCK_COPY_PASTE = { copyPaste: { drawing: false, selection: MOCK_SELECTION } };

    const MOCK_STATE = {
      'react-planner': {
        ...MOCK_COPY_PASTE,
      },
    };
    renderComponent(MOCK_STATE);

    expect(screen.getByText(/Copy lines drawing a rectangle/)).toBeInTheDocument();
    expect(screen.queryByText(/To paste in a different plan/)).toBeInTheDocument();
  });

  it('Renders instructions to paste the annotations from other plan', () => {
    const MOCK_COPY_PASTE_STORAGE = '{"elements":{},"selection":{},"planId":2}';
    jest.spyOn(ProviderStorage, 'get').mockImplementation(() => MOCK_COPY_PASTE_STORAGE);

    renderComponent();

    expect(screen.getByText(/Copied annotations from other plan detected/)).toBeInTheDocument();
    expect(screen.queryByText(/Copy lines drawing a rectangle/)).not.toBeInTheDocument();
  });
});
