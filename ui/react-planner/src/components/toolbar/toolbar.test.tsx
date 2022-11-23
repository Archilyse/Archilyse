import * as React from 'react';
import thunk from 'redux-thunk';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { render } from '@testing-library/react';
import configureStore from 'redux-mock-store';
import { MOCK_STATE } from '../../tests/utils';
import {
  CLOSE_SNACKBAR,
  DISABLE_SCALING,
  ENABLE_SCALING,
  MODE_COPY_PASTE,
  MODE_IDLE,
  MODE_ROTATE_SCALE_BACKGROUND,
  SeparatorsType,
  SET_MODE,
} from '../../constants';
import { Models as PlannerModels } from '../../export'; //react-planner
import Toolbar from './toolbar';

const AppState = {
  'react-planner': new PlannerModels.State(),
};

jest.mock('react-router-dom', () => ({
  useParams() {
    return jest.fn();
  },
}));

// @TODO: Erase it once scale/rotate button toolbar is visible for anyone
jest.mock('archilyse-ui-components', () => {
  /* eslint-disable */
  const React = require('react');
  const C = require('../../constants');
  /* eslint-enable */

  return {
    // @ts-ignore
    ...jest.requireActual('archilyse-ui-components'),
    getUserRoles: () => [C.ROLES.ADMIN],
  };
});

describe('Toolbar component', () => {
  let props;
  let store;
  const mockStore = configureStore([thunk]);
  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <Toolbar {...props} />
      </Provider>
    );
  };

  beforeEach(() => {
    const newState = {
      'react-planner': {
        ...AppState['react-planner'],
        scaleValidated: true,
      },
    };
    store = mockStore(newState);
    props = {
      width: 120,
      height: 30,
    };
  });

  afterEach(() => {
    store.clearActions();
  });

  describe('Renders buttons', () => {
    it.each([
      ['Save project'],
      ['Open catalog'],
      ['Select tool'],
      ['Undo (CTRL-Z)'],
      ['Scale tool'],
      ['Help'],
      ['Copy & paste tool'],
    ])('With scale validated, renders: %s', async tooltip => {
      const { container } = renderComponent();
      const toolbarButton = container.querySelector(`[tooltip="${tooltip}"]`);
      expect(toolbarButton).toBeInTheDocument();
    });

    it.each([['Save project'], ['Open catalog'], ['Copy & paste tool']])(
      'Without scale validated, does not render: %s',
      async tooltip => {
        const newState = {
          'react-planner': {
            ...AppState['react-planner'],
            scaleValidated: false,
          },
        };
        store = mockStore(newState);
        const { container } = renderComponent();
        const toolbarButton = container.querySelector(`[tooltip="${tooltip}"]`);
        expect(toolbarButton).not.toBeInTheDocument();
      }
    );
    it.each([['Select tool'], ['Undo (CTRL-Z)'], ['Scale tool'], ['Help']])(
      'Without scaled validate, renders: %s',
      async tooltip => {
        const newState = {
          'react-planner': {
            ...AppState['react-planner'],
            scaleValidated: false,
          },
        };
        store = mockStore(newState);
        const { container } = renderComponent();
        const toolbarButton = container.querySelector(`[tooltip="${tooltip}"]`);
        expect(toolbarButton).toBeInTheDocument();
      }
    );
  });

  describe('Scale tool button', () => {
    it('Is not visible if the user must import annotations', () => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          drawingSupport: {},
          mode: MODE_IDLE,
          mustImportAnnotations: true,
        },
      };
      store = mockStore(newState);

      const { container } = renderComponent();
      const scaleButton = container.querySelector(`[tooltip="Scale tool"]`);
      expect(scaleButton).not.toBeInTheDocument();
    });
    it('Clicking on it with mode idle enables scaling', () => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          drawingSupport: {},
          mode: MODE_IDLE,
        },
      };
      store = mockStore(newState);

      const { container } = renderComponent();
      const scaleButton = container.querySelector(`[tooltip="Scale tool"]`);
      userEvent.click(scaleButton);
      const [firstAction] = store.getActions();

      expect(firstAction.type).toBe(ENABLE_SCALING);
    });

    it('Clicking on it with scaling enabled disables it', () => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          drawingSupport: {
            type: SeparatorsType.SCALE_TOOL,
          },
        },
      };
      store = mockStore(newState);

      const { container } = renderComponent();
      const scaleButton = container.querySelector(`[tooltip="Scale tool"]`);
      userEvent.click(scaleButton);

      const [action1, action2] = store.getActions();

      expect(action1.type).toBe(DISABLE_SCALING);
      expect(action2.type).toBe(CLOSE_SNACKBAR);
    });

    it('Clicking on Copy & paste tool with scaling enabled will disable scaling and enable copy/paste mode', () => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          drawingSupport: {
            type: SeparatorsType.SCALE_TOOL,
          },
        },
      };
      store = mockStore(newState);
      const { container } = renderComponent();

      const copyPasteTooltip = 'Copy & paste tool';

      const copyPasteButton = container.querySelector(`[tooltip="${copyPasteTooltip}"]`);
      userEvent.click(copyPasteButton);
      const [action1, action2] = store.getActions();
      expect(action1.type).toBe(DISABLE_SCALING);
      expect(action2.type).toBe(SET_MODE);
      expect(action2.mode).toBe(MODE_COPY_PASTE);
    });
  });

  describe('Setting modes', () => {
    it.each([
      ['Rotate/scale background', MODE_ROTATE_SCALE_BACKGROUND],
      ['Copy & paste tool', MODE_COPY_PASTE],
    ])('Clicking on %s sets mode: %s', async (tooltip, expectedMode) => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          mode: MODE_IDLE,
        },
      };
      store = mockStore(newState);
      const { container } = renderComponent();

      // If we click once, the mode is enabled
      const leftToolbarButton = container.querySelector(`[tooltip="${tooltip}"]`);
      userEvent.click(leftToolbarButton);
      const setModeAction = store.getActions().find(({ type }) => type === SET_MODE);
      expect(setModeAction.mode).toBe(expectedMode);
    });

    it.each([
      ['Rotate/scale background', MODE_ROTATE_SCALE_BACKGROUND],
      ['Copy & paste tool', MODE_COPY_PASTE],
    ])('Clicking on %s unsets mode: %s', async (tooltip, initialMode) => {
      const newState = {
        'react-planner': {
          ...AppState['react-planner'],
          ...MOCK_STATE,
          mode: initialMode,
        },
      };
      store = mockStore(newState);
      const { container } = renderComponent();

      // If we click once, the mode is enabled
      const leftToolbarButton = container.querySelector(`[tooltip="${tooltip}"]`);
      userEvent.click(leftToolbarButton);
      const setModeAction = store.getActions().find(({ type }) => type === SET_MODE);
      expect(setModeAction.mode).toBe(MODE_IDLE);
    });
  });
});
