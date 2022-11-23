import React from 'react';
import { createStore } from 'redux';
import thunk from 'redux-thunk';
import { Provider } from 'react-redux';
import { fireEvent, render } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import configureStore from 'redux-mock-store';
import MyCatalog from '../catalog-elements/mycatalog';
import { rotateSelectedDoors } from '../actions/holes-actions';
import {
  remove,
  rollback,
  setAlterateState,
  setCtrlKeyActive,
  setShowBackgroundOnly,
  toggleCatalogToolbar,
  toggleSnap,
  undo,
} from '../actions/project-actions';
import { changeReferenceLine, decreaseWidthSelectedWalls, increaseWidthSelectedWalls } from '../actions/lines-actions';
import { Models as PlannerModels, Plugins as PlannerPlugins, reducer as PlannerReducer, ReactPlanner } from '../export'; //react-planner
import { MOCK_AUTHENTICATION, MOCK_SCENE } from '../tests/utils';

// Real state & reducer used in renderer.jsx
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

describe('Keyboard shortcuts', () => {
  let props;
  let store;
  const mockStore = configureStore([thunk]);
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps, store };
    return render(
      <Provider store={store}>
        <MemoryRouter initialEntries={['/1']}>
          <Route path="/:id">
            <ReactPlanner {...props} />
          </Route>
        </MemoryRouter>
      </Provider>
    );
  };

  const plugins = [PlannerPlugins.Keyboard()];

  beforeEach(() => {
    MOCK_AUTHENTICATION();

    props = {
      catalog: MyCatalog,
      width: 3000,
      height: 2000,
      plugins,
      stateExtractor: state => state['react-planner'],
    };
    store = mockStore(AppState);
  });

  afterEach(() => {
    store.clearActions();
  });

  // @TODO:Add missing tests arrowUp, arrowDown... as they do not dispatch an action but call a different function
  it.each([
    [{ key: 'Backspace' }, remove],
    [{ key: 'Delete' }, remove],
    [{ key: 'Escape' }, rollback],
    [{ key: ' ' }, setShowBackgroundOnly.bind(null, true)],
    [{ key: 'l' }, toggleCatalogToolbar],
    [{ key: 'r' }, rotateSelectedDoors],
    [{ key: 'z', ctrlKey: true }, undo],
    [{ key: 'x', ctrlKey: true }, toggleSnap],
    [{ key: 'f' }, changeReferenceLine],
    [{ key: '+' }, increaseWidthSelectedWalls],
    [{ key: '-' }, decreaseWidthSelectedWalls],
    [{ key: 'Control' }, setAlterateState.bind(null, true)],
  ])('Pressing (keyDown) the key %p triggers the action:', async (keyEvent, expectedActionCreator) => {
    const { container } = renderComponent();
    fireEvent.keyDown(container, keyEvent);
    const expectedAction = expectedActionCreator();
    const dispatchedActions = store.getActions();
    const exptectedDispatchedAction = dispatchedActions.find(action => action.type === expectedAction.type);
    expect(exptectedDispatchedAction).toMatchObject(expectedAction);
  });

  it.each([
    [{ key: 'Control' }, setAlterateState.bind(null, false)],
    [{ key: ' ' }, setShowBackgroundOnly.bind(null, false)],
  ])('Releasing (keyUp) the key %o triggers the action:', async (keyEvent, expectedActionCreator) => {
    const { container } = renderComponent();
    fireEvent.keyUp(container, keyEvent);
    const expectedAction = expectedActionCreator();
    const dispatchedActions = store.getActions();
    const exptectedDispatchedAction = dispatchedActions.find(action => action.type === expectedAction.type);
    expect(exptectedDispatchedAction).toMatchObject(expectedAction);
  });

  it('Can select multiple annotations and unselect them with CTRL pressed (keyDown)', () => {
    const getSelectedAnnotations = (store, selectedLayer, firstLineId, secondLineId, itemId, holeId) => {
      const layer = store.getState()['react-planner'].scene.layers[selectedLayer];
      const allSelected = layer.selected;
      const selectedLines = allSelected.lines;
      const selectedItems = allSelected.items;
      const selectedHoles = allSelected.holes;

      const firstLineSelected = layer.lines[firstLineId].selected;
      const secondLineSelected = layer.lines[secondLineId].selected;
      const itemSelected = layer.items[itemId].selected;
      const holeSelected = layer.holes[holeId].selected;

      return {
        selectedLines,
        selectedItems,
        selectedHoles,
        firstLineSelected,
        secondLineSelected,
        itemSelected,
        holeSelected,
      };
    };
    const storeWithState = createStore(reducer, null);
    store = {
      ...store, // this store has actions history, but doesn't set the actual state
      ...storeWithState, // this store sets the actual state
    };
    const selectedLayer = MOCK_SCENE.selectedLayer;
    const newState = {
      'react-planner': {
        scene: {
          ...MOCK_SCENE,
        },
      },
    };
    const action = { type: 'SET_NEW', data: newState };
    store.dispatch(action); // setting mock scene with mock annotations (i.e. lines, holes etc)

    const firstLineId = '4db6ed77-c27e-41c8-91b5-26fc94813982'; // from MOCK_SCENE
    const secondLineId = 'a1b39c85-1113-4103-b713-1e6f0c20d1a1'; // from MOCK_SCENE
    const itemId = 'f06b6b06-b4f4-4500-83c9-1cca2b8c5876'; // from MOCK_SCENE
    const holeId = 'c1db052f-b665-4c24-9b08-dd8efa320ce9'; // from MOCK_SCENE

    const { container, getByTestId } = renderComponent();
    // Select first line
    fireEvent.mouseUp(getByTestId(`viewer-line-${firstLineId}`));
    // Press CTRL
    const ctrlkeyEvent = { key: 'Control' };
    fireEvent.keyDown(container, ctrlkeyEvent);
    // Select second line
    fireEvent.mouseUp(getByTestId(`viewer-line-${secondLineId}`));
    // Select item
    fireEvent.mouseUp(getByTestId(`viewer-item-${itemId}`));
    // Select hole
    fireEvent.mouseUp(getByTestId(`hole-${holeId}`));

    const {
      selectedLines,
      selectedItems,
      selectedHoles,
      firstLineSelected,
      secondLineSelected,
      itemSelected,
      holeSelected,
    } = getSelectedAnnotations(store, selectedLayer, firstLineId, secondLineId, itemId, holeId);
    expect(selectedLines.length).toBe(2);
    expect(selectedLines[0]).toBe(firstLineId);
    expect(selectedLines[1]).toBe(secondLineId);
    expect(firstLineSelected).toBe(true);
    expect(secondLineSelected).toBe(true);

    expect(selectedItems.length).toBe(1);
    expect(selectedItems[0]).toBe(itemId);
    expect(selectedHoles.length).toBe(1);
    expect(selectedHoles[0]).toBe(holeId);
    expect(itemSelected).toBe(true);
    expect(holeSelected).toBe(true);

    // Unselect annotations (CTRL is already pressed)
    fireEvent.mouseUp(getByTestId(`viewer-line-${firstLineId}`));
    fireEvent.mouseUp(getByTestId(`viewer-line-${secondLineId}`));
    fireEvent.mouseUp(getByTestId(`viewer-item-${itemId}`));
    fireEvent.mouseUp(getByTestId(`hole-${holeId}`));

    const {
      selectedLines: selectedLinesAfterUnselect,
      selectedItems: selectedItemsAfterUnselect,
      selectedHoles: selectedHolesAfterUnselect,
      firstLineSelected: firstLineSelectedAfterUnselect,
      secondLineSelected: secondLineSelectedAfterUnselect,
      itemSelected: itemSelectedAfterUnselect,
      holeSelected: holeSelectedAfterUnselect,
    } = getSelectedAnnotations(store, selectedLayer, firstLineId, secondLineId, itemId, holeId);
    expect(selectedLinesAfterUnselect.length).toBe(0);
    expect(selectedItemsAfterUnselect.length).toBe(0);
    expect(selectedHolesAfterUnselect.length).toBe(0);
    expect(firstLineSelectedAfterUnselect).toBe(false);
    expect(secondLineSelectedAfterUnselect).toBe(false);
    expect(itemSelectedAfterUnselect).toBe(false);
    expect(holeSelectedAfterUnselect).toBe(false);
  });

  it('Can select multiple annotations with CTRL pressed (keyDown) and delete them', () => {
    const getSelectedLines = (store, selectedLayer, firstLineId, secondLineId) => {
      const layer = store.getState()['react-planner'].scene.layers[selectedLayer];
      const selectedLines = layer.selected.lines;
      const firstLineSelected = layer.lines[firstLineId]?.selected;
      const secondLineSelected = layer.lines[secondLineId]?.selected;

      return { selectedLines, firstLineSelected, secondLineSelected };
    };
    const storeWithState = createStore(reducer, null);
    store = {
      ...store, // this store has actions history, but doesn't set the actual state
      ...storeWithState, // this store sets the actual state
    };
    const selectedLayer = MOCK_SCENE.selectedLayer;
    const newState = {
      'react-planner': {
        scene: {
          ...MOCK_SCENE,
        },
      },
    };
    const action = { type: 'SET_NEW', data: newState };
    store.dispatch(action); // setting mock scene with mock annotations (i.e. lines, holes etc)

    const firstLineId = '4db6ed77-c27e-41c8-91b5-26fc94813982'; // from MOCK_SCENE
    const secondLineId = 'a1b39c85-1113-4103-b713-1e6f0c20d1a1'; // from MOCK_SCENE

    const { container, getByTestId } = renderComponent();
    // Select first line
    fireEvent.mouseUp(getByTestId(`viewer-line-${firstLineId}`));
    // Press CTRL
    const ctrlkeyEvent = { key: 'Control' };
    fireEvent.keyDown(container, ctrlkeyEvent);
    // Select second line
    fireEvent.mouseUp(getByTestId(`viewer-line-${secondLineId}`));

    const { selectedLines, firstLineSelected, secondLineSelected } = getSelectedLines(
      store,
      selectedLayer,
      firstLineId,
      secondLineId
    );
    expect(selectedLines.length).toBe(2);
    expect(selectedLines[0]).toBe(firstLineId);
    expect(selectedLines[1]).toBe(secondLineId);
    expect(firstLineSelected).toBe(true);
    expect(secondLineSelected).toBe(true);

    // Delete selected lines
    const deletekeyEvent = { key: 'Delete' };
    fireEvent.keyDown(container, deletekeyEvent);

    const {
      selectedLines: selectedLinesAfterDelete,
      firstLineSelected: firstLineSelectedAfterDelete,
      secondLineSelected: secondLineSelectedAfterDelete,
    } = getSelectedLines(store, selectedLayer, firstLineId, secondLineId);
    expect(selectedLinesAfterDelete.length).toBe(0);
    expect(firstLineSelectedAfterDelete).not.toBeDefined();
    expect(secondLineSelectedAfterDelete).not.toBeDefined();
  });

  describe('With multiple annotations selected', () => {
    const mockStore = configureStore();
    beforeEach(() => {
      const selectedAnnotations = { lines: ['one', 'two'] };
      const newAppState = {
        'react-planner': {
          ...AppState['react-planner'],
          scene: {
            ...AppState['react-planner'].scene,
            layers: {
              ...AppState['react-planner'].scene.layers,
              ['layer-1']: {
                ...AppState['react-planner'].scene.layers['layer-1'],
                selected: {
                  ...AppState['react-planner'].scene.layers['layer-1'].selected,
                  ...selectedAnnotations,
                },
              },
            },
          },
        },
      };
      const storeWithActionsHistory = mockStore(newAppState);
      store = storeWithActionsHistory;
    });

    afterEach(() => {
      store.clearActions();
    });

    it('Pressing (keyDown) and Releasing (keyUp) the key CTRL will dispatch SET_CTRL_KEY_ACTIVE action', () => {
      const keyEvent = { key: 'Control' };
      const expectedActionCreator = setCtrlKeyActive;
      const expectedActionType = expectedActionCreator(true).type;
      const { container } = renderComponent();
      fireEvent.keyDown(container, keyEvent); // payload: true
      fireEvent.keyUp(container, keyEvent); // payload: false
      const actions = store.getActions();
      const dispatchedActions = actions.filter(action => action.type === expectedActionType);
      expect(dispatchedActions.length).toBe(2);
      const [firstDispatchedAction, secondDispatchedAction] = dispatchedActions;
      expect(firstDispatchedAction.payload).toBe(true);
      expect(secondDispatchedAction.payload).toBe(false);
    });

    it.each([
      [{ key: 'r' }, rotateSelectedDoors],
      [{ key: '+' }, increaseWidthSelectedWalls],
      [{ key: '-' }, decreaseWidthSelectedWalls],
      [{ key: 'Control' }, setAlterateState.bind(null, true)],
    ])('Pressing (keyDown) the key %p does not trigger the action:', async (keyEvent, expectedActionCreator) => {
      const { container } = renderComponent();
      fireEvent.keyDown(container, keyEvent);
      const actions = store.getActions();
      const expectedActionType = expectedActionCreator().type;
      const dispatchedAction = actions.find(action => action.type === expectedActionType);

      expect(dispatchedAction).not.toBeDefined();
    });
  });
});
