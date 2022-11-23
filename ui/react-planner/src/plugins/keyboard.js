import { batch } from 'react-redux';
import {
  KEYBOARD_KEYS,
  MODE_COPY_PASTE,
  MODE_IDLE,
  MODE_RECTANGLE_TOOL,
  REQUEST_STATUS_BY_ACTION,
  RequestStatusType,
} from '../constants';
import {
  fitToScreen,
  onSaveProjectSuccessfull,
  remove,
  rollback,
  saveProjectAsync,
  setAlterateState,
  setCtrlKeyActive,
  setShowBackgroundOnly,
  showSnackbar,
  toggleCatalogToolbar,
  toggleSnap,
  undo,
} from '../actions/project-actions';
import {
  copySelectedHole,
  decreaseWidthSelectedHoles,
  increaseWidthSelectedHoles,
  rotateSelectedDoors,
} from '../actions/holes-actions';
import {
  copySelectedItem,
  decreaseLengthSelectedItems,
  decreaseWidthSelectedItems,
  increaseLengthSelectedItems,
  increaseWidthSelectedItems,
} from '../actions/items-actions';
import { changeReferenceLine, decreaseWidthSelectedWalls, increaseWidthSelectedWalls } from '../actions/lines-actions';
import { restoreCopyPasteFromAnotherPlan, saveCopyPasteSelection } from '../actions/copy-paste-actions';
import hasCopyPasteFromAnotherPlan from '../utils/has-copy-paste-from-another-plan';
import getSelectedAnnotationsSize from '../utils/get-selected-annotations-size';
import hasProjectChanged from '../utils/has-project-changed';
import isScaling from '../utils/is-scaling';

const triggerKeyboardArrowsAction = (store, state, event) => {
  event.preventDefault();

  const keyMapActions = {
    [KEYBOARD_KEYS.ARROW_RIGHT]: 'increaseWidth',
    [KEYBOARD_KEYS.ARROW_LEFT]: 'decreaseWidth',
    [KEYBOARD_KEYS.ARROW_UP]: 'increaseLength',
    [KEYBOARD_KEYS.ARROW_DOWN]: 'decreaseLength',
  };

  const actions = {
    increaseWidthSelectedHoles,
    decreaseWidthSelectedHoles,
    increaseWidthSelectedItems,
    decreaseWidthSelectedItems,
    increaseLengthSelectedItems,
    decreaseLengthSelectedItems,
  };

  const action = keyMapActions[event.key];

  const selectedLayer = state.scene.selectedLayer;
  const selected = state.scene.layers[selectedLayer].selected;
  const pendingDispatches = [];

  ['Holes', 'Items'].forEach(prototype => {
    const actionName = [action, 'Selected', prototype].join('');
    if (selected[prototype.toLowerCase()].length && actions.hasOwnProperty(actionName)) {
      pendingDispatches.push(actions[actionName]);
    }
  });

  pendingDispatches.forEach(dispatchable => store.dispatch(dispatchable()));
};

const triggerCopyAction = (store, state, event) => {
  event.preventDefault();

  const selectedLayer = state.scene.selectedLayer;
  const selected = state.scene.layers[selectedLayer].selected;

  let action = null;

  if (selected.items.length === 1) {
    action = copySelectedItem;
  } else if (selected.holes.length === 1) {
    action = copySelectedHole;
  }

  action && store.dispatch(action());
};

const triggerCtrlAction = (store, state, payload) => {
  const isCtrlActive = state.ctrlActive;
  const selectedAnnotationsSize = getSelectedAnnotationsSize(state);
  const noAnnotationsSelected = selectedAnnotationsSize === 0;
  if (noAnnotationsSelected) {
    batch(() => {
      store.dispatch(setAlterateState(payload));
      // set ctrlActive to false, this must be done when doing CTRL + C on an item
      payload === false && isCtrlActive && store.dispatch(setCtrlKeyActive(payload));
    });
  } else {
    store.dispatch(setCtrlKeyActive(payload));
  }
};

const execIfOnlyOneAnnotationSelected = (state, cb) => {
  const selectedAnnotationsSize = getSelectedAnnotationsSize(state);
  if (selectedAnnotationsSize < 2) {
    cb();
  }
};

const isCtrlPressed = event => event.getModifierState('Control') || event.getModifierState('Meta') || event.ctrlKey;

export default function keyboard() {
  return (store, stateExtractor) => {
    window.addEventListener('keydown', event => {
      const state = stateExtractor(store.getState());
      const mode = state.mode;

      switch (event.key) {
        case KEYBOARD_KEYS.BACKSPACE:
        case KEYBOARD_KEYS.DELETE: {
          if ([MODE_IDLE, MODE_RECTANGLE_TOOL].includes(mode)) store.dispatch(remove());
          break;
        }
        case KEYBOARD_KEYS.ESCAPE: {
          store.dispatch(rollback());
          break;
        }
        case KEYBOARD_KEYS.SPACE: {
          store.dispatch(setShowBackgroundOnly(true));
          break;
        }
        case KEYBOARD_KEYS.X: {
          if (isCtrlPressed(event)) {
            store.dispatch(toggleSnap());
          }
          break;
        }
        case KEYBOARD_KEYS.Z: {
          if (isCtrlPressed(event)) {
            const isAlterateActive = state.alterate;
            store.dispatch(undo());
            isAlterateActive && store.dispatch(setAlterateState(false));
          } else {
            store.dispatch(fitToScreen());
          }
          break;
        }
        case KEYBOARD_KEYS.S: {
          if (isCtrlPressed(event)) {
            event.preventDefault();

            const planId = state.planInfo.id;
            const sceneRequestStatus = state.requestStatus[REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS];

            const isModifyingProject = state.mode !== MODE_IDLE || isScaling(state);
            const isLoading = sceneRequestStatus && sceneRequestStatus.status === RequestStatusType.PENDING;
            const projectHasChanges = hasProjectChanged(state);

            if (!isLoading && projectHasChanges && !isModifyingProject) {
              store.dispatch(
                saveProjectAsync(
                  { planId, state, validated: true },
                  {
                    onFulfill: project => store.dispatch(onSaveProjectSuccessfull(project)),
                    onReject: error => {
                      let msg = 'Error occured while saving a project';
                      if (error?.response?.data?.msg) {
                        msg += `: ${error?.response?.data?.msg}`;
                      }
                      store.dispatch(
                        showSnackbar({
                          message: msg,
                          severity: 'error',
                        })
                      );
                    },
                  }
                )
              );
            }
          }
          break;
        }
        // @TODO: Use a better letter for this
        case KEYBOARD_KEYS.F: {
          store.dispatch(changeReferenceLine());
          break;
        }
        case KEYBOARD_KEYS.L: {
          store.dispatch(toggleCatalogToolbar());
          break;
        }
        case KEYBOARD_KEYS.R: {
          execIfOnlyOneAnnotationSelected(state, () => {
            store.dispatch(rotateSelectedDoors());
          });
          break;
        }
        case KEYBOARD_KEYS.PLUS: {
          execIfOnlyOneAnnotationSelected(state, () => {
            store.dispatch(increaseWidthSelectedWalls());
          });
          break;
        }
        case KEYBOARD_KEYS.MINUS: {
          execIfOnlyOneAnnotationSelected(state, () => {
            store.dispatch(decreaseWidthSelectedWalls());
          });
          break;
        }
        case KEYBOARD_KEYS.CTRL: {
          triggerCtrlAction(store, state, true);
          break;
        }
        case KEYBOARD_KEYS.ARROW_UP:
        case KEYBOARD_KEYS.ARROW_DOWN:
        case KEYBOARD_KEYS.ARROW_LEFT:
        case KEYBOARD_KEYS.ARROW_RIGHT: {
          execIfOnlyOneAnnotationSelected(state, () => {
            if (isCtrlPressed(event)) {
              triggerKeyboardArrowsAction(store, state, event);
            }
          });
          break;
        }
        case KEYBOARD_KEYS.C: {
          if (isCtrlPressed(event)) {
            triggerCopyAction(store, state, event);
          }
          break;
        }
        case KEYBOARD_KEYS.V: {
          if (isCtrlPressed(event)) {
            const planId = state.planInfo.id;
            const hasScaleBeenValidated = state.scaleValidated;
            if (hasCopyPasteFromAnotherPlan(planId) && hasScaleBeenValidated) {
              store.dispatch(restoreCopyPasteFromAnotherPlan());
            }
            if (mode === MODE_COPY_PASTE) {
              store.dispatch(saveCopyPasteSelection());
            }
          }
          break;
        }
      }
    });

    window.addEventListener('keyup', event => {
      const state = stateExtractor(store.getState());
      switch (event.key) {
        case KEYBOARD_KEYS.CTRL: {
          triggerCtrlAction(store, state, false);
          break;
        }
        case KEYBOARD_KEYS.SPACE: {
          store.dispatch(setShowBackgroundOnly(false));
          break;
        }
      }
    });
  };
}
