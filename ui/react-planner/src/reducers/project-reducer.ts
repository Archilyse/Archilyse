import { history } from '../utils/export';
import {
  ALTERATE_STATE,
  CLEAR_SCALE_DRAWING,
  CLOSE_SNACKBAR,
  COPY_PROPERTIES,
  DISABLE_SCALING,
  ENABLE_SCALING,
  FIT_SCREEN,
  GET_PREDICTION_FULFILLED,
  GET_PREDICTION_PENDING,
  GET_PREDICTION_REJECTED,
  GET_PROJECT_FULFILLED,
  GET_PROJECT_PENDING,
  GET_PROJECT_REJECTED,
  INIT_CATALOG,
  LOAD_PROJECT,
  MODE_IDLE,
  NEW_PROJECT,
  PASTE_PROPERTIES,
  PUSH_LAST_SELECTED_CATALOG_ELEMENT_TO_HISTORY,
  REGENERATE_AREAS,
  REMOVE,
  REMOVE_SCALING_LINES,
  REQUEST_STATUS_BY_ACTION,
  ROLLBACK,
  SAVE_PROJECT_FULFILLED,
  SAVE_PROJECT_PENDING,
  SAVE_PROJECT_REJECTED,
  SELECT_TOOL_EDIT,
  SET_ANNOTATION_FINISHED,
  SET_BACKGROUND_DIMENSIONS,
  SET_BACKGROUND_ROTATION,
  SET_BACKGROUND_SHIFT,
  SET_CTRL_KEY_ACTIVE,
  SET_HIGHLIGHTED_ERROR,
  SET_MODE,
  SET_MUST_IMPORT_ANNOTATIONS,
  SET_PLAN_INFO,
  SET_PROJECT_HASH_CODE,
  SET_PROJECT_PROPERTIES,
  SET_PROPERTIES,
  SET_SCALE_TOOL_PROPERTIES,
  SET_SCALE_VALIDATED,
  SET_SCENE_DIMENSIONS,
  SET_SCENE_PROPERTIES,
  SET_SHOW_BACKGROUND_ONLY,
  SET_VALIDATION_ERRORS,
  SHOW_SNACKBAR,
  THROW_ERROR,
  THROW_WARNING,
  TOGGLE_AUTOLABELLING_FEEDBACK,
  TOGGLE_CATALOG_TOOLBAR,
  TOGGLE_SHOW_SNAP_ELEMENTS,
  TOGGLE_SNAP,
  UNDO,
  UNSELECT_ALL,
} from '../constants';

import { Project } from '../class/export';
import RequestStatus from '../class/request-status';

export default (state, action) => {
  switch (action.type) {
    case NEW_PROJECT:
      return Project.newProject(state).updatedState;

    case LOAD_PROJECT:
      return Project.loadProject(state, action.sceneJSON).updatedState;

    case GET_PROJECT_PENDING:
      return RequestStatus.setPending(state, REQUEST_STATUS_BY_ACTION.GET_PLAN_ANNOTATIONS);

    case GET_PROJECT_FULFILLED: {
      state = Project.loadProject(state, action.payload.data).updatedState;
      return RequestStatus.setFulfilled(state, REQUEST_STATUS_BY_ACTION.GET_PLAN_ANNOTATIONS);
    }

    case GET_PROJECT_REJECTED:
      return RequestStatus.setRejected(state, REQUEST_STATUS_BY_ACTION.GET_PLAN_ANNOTATIONS, action.error);

    case GET_PREDICTION_PENDING:
      return RequestStatus.setPending(state, REQUEST_STATUS_BY_ACTION.GET_PREDICTION);

    case GET_PREDICTION_FULFILLED: {
      state = Project.loadPrediction(state, action.payload).updatedState;
      return RequestStatus.setFulfilled(state, REQUEST_STATUS_BY_ACTION.GET_PREDICTION);
    }

    case GET_PREDICTION_REJECTED:
      return RequestStatus.setRejected(state, REQUEST_STATUS_BY_ACTION.GET_PREDICTION, action.error);

    case SAVE_PROJECT_PENDING:
      return RequestStatus.setPending(state, REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS);

    case SAVE_PROJECT_FULFILLED: {
      const updatedState = Project.loadProject(state, action.payload.data).updatedState;
      return RequestStatus.setFulfilled(updatedState, REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS);
    }

    case SAVE_PROJECT_REJECTED:
      return RequestStatus.setRejected(state, REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS, action.error);

    case SELECT_TOOL_EDIT:
      return Project.setMode(state, MODE_IDLE).updatedState;

    case UNSELECT_ALL:
      return Project.unselectAll(state).updatedState;

    case SET_PROPERTIES:
      return Project.setProperties(state, state.scene.selectedLayer, action.properties).updatedState;

    case REMOVE:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Project.remove(state).updatedState;

    case UNDO:
      return Project.undo(state).updatedState;

    case FIT_SCREEN:
      return Project.fitScreen(state).updatedState;

    case ROLLBACK:
      return Project.rollback(state).updatedState;

    case SET_PROJECT_PROPERTIES:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Project.setProjectProperties(state, action.properties).updatedState;

    case ENABLE_SCALING:
      return Project.enableScaling(state).updatedState;

    case DISABLE_SCALING:
      return Project.disableScaling(state).updatedState;

    case CLEAR_SCALE_DRAWING:
      return Project.clearScaleDrawing(state).updatedState;

    case REMOVE_SCALING_LINES:
      return Project.removeScalingLines(state).updatedState;

    case SET_SCALE_TOOL_PROPERTIES:
      return Project.setScaleToolProperties(state, action.payload).updatedState;

    case SET_SCENE_PROPERTIES:
      return Project.setSceneProperties(state, action.payload).updatedState;

    case SET_PROJECT_HASH_CODE:
      return Project.setProjectHashCode(state).updatedState;

    case INIT_CATALOG:
      return Project.initCatalog(state, action.catalog).updatedState;

    case TOGGLE_CATALOG_TOOLBAR:
      return Project.toggleCatalogToolbar(state).updatedState;

    case TOGGLE_AUTOLABELLING_FEEDBACK:
      return Project.toggleAutoLabellingFeedback(state).updatedState;

    case TOGGLE_SNAP:
      return Project.toggleSnap(state, action.mask).updatedState;

    case TOGGLE_SHOW_SNAP_ELEMENTS:
      return Project.toggleShowSnapElements(state).updatedState;

    case THROW_ERROR:
      return Project.throwError(state, action.error).updatedState;

    case THROW_WARNING:
      return Project.throwWarning(state, action.warning).updatedState;

    case COPY_PROPERTIES:
      return Project.copyProperties(state, action.properties).updatedState;

    case PASTE_PROPERTIES:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Project.pasteProperties(state).updatedState;

    case PUSH_LAST_SELECTED_CATALOG_ELEMENT_TO_HISTORY:
      return Project.pushLastSelectedCatalogElementToHistory(state, action.element).updatedState;

    case ALTERATE_STATE:
      return Project.setAlterate(state, action.payload).updatedState;

    case SET_CTRL_KEY_ACTIVE: {
      state.ctrlActive = action.payload;
      return state;
    }

    case SET_MODE:
      return Project.setMode(state, action.mode).updatedState;

    case SET_HIGHLIGHTED_ERROR:
      return Project.setHighlightedError(state, action.payload).updatedState;

    case SET_VALIDATION_ERRORS:
      return Project.setValidationErrors(state, action.payload).updatedState;

    case REGENERATE_AREAS:
      return Project.regenerateAreas(state).updatedState;

    case SET_ANNOTATION_FINISHED:
      return Project.setAnnotationFinished(state, action.payload).updatedState;

    case SET_MUST_IMPORT_ANNOTATIONS:
      return Project.mustImportAnnotations(state, action.payload).updatedState;

    case SET_SCENE_DIMENSIONS:
      return Project.setSceneDimensions(state, action.payload).updatedState;

    case SET_BACKGROUND_DIMENSIONS:
      return Project.setBackgroundDimensions(state, action.payload).updatedState;

    case SET_BACKGROUND_ROTATION:
      return Project.setBackgroundRotation(state, action.payload).updatedState;

    case SET_BACKGROUND_SHIFT:
      return Project.setBackgroundShift(state, action.payload).updatedState;

    case SET_SHOW_BACKGROUND_ONLY:
      return Project.setShowBackgroundOnly(state, action.payload).updatedState;

    case SET_SCALE_VALIDATED:
      return Project.setScaleValidated(state, action.payload).updatedState;

    case SET_PLAN_INFO:
      return Project.setPlanInfo(state, action.payload).updatedState;

    case SHOW_SNACKBAR:
      return Project.showSnackbar(state, action.payload).updatedState;

    case CLOSE_SNACKBAR:
      return Project.closeSnackbar(state, action.payload).updatedState;

    default:
      return state;
  }
};
