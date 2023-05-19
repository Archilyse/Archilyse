import { batch } from 'react-redux';
import isScaling from '../utils/is-scaling';
import cloneDeep from '../utils/clone-deep';
import getLabellingPrediction from '../utils/get-labelling-prediction';
import { ProviderRequest } from '../providers';
import Project from '../class/project';
import Layer from '../class/layer';
import {
  ALTERATE_STATE,
  CLEAR_SCALE_DRAWING,
  CLOSE_SNACKBAR,
  COPY_PROPERTIES,
  DISABLE_SCALING,
  ENABLE_SCALING,
  ENDPOINTS,
  FIT_SCREEN,
  GET_PREDICTION_FULFILLED,
  GET_PREDICTION_PENDING,
  GET_PREDICTION_REJECTED,
  GET_PROJECT_FULFILLED,
  GET_PROJECT_PENDING,
  GET_PROJECT_REJECTED,
  INIT_CATALOG,
  LOAD_PROJECT,
  NEW_PROJECT,
  PASTE_PROPERTIES,
  PUSH_LAST_SELECTED_CATALOG_ELEMENT_TO_HISTORY,
  REGENERATE_AREAS,
  REMOVE,
  REMOVE_SCALING_LINES,
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
import getSelectedAnnotationsSize from '../utils/get-selected-annotations-size';
import { Area, Prediction } from '../types';
import * as planActions from './plan-actions';

const STILL_THERE_MS = 45 * 1000;

export function loadProject(sceneJSON) {
  return {
    type: LOAD_PROJECT,
    sceneJSON,
  };
}

export function fitToScreen() {
  return {
    type: FIT_SCREEN,
  };
}

export function newProject() {
  return {
    type: NEW_PROJECT,
  };
}

export function getProjectPending() {
  return {
    type: GET_PROJECT_PENDING,
  };
}

export function getProjectFulfilled(payload) {
  return {
    type: GET_PROJECT_FULFILLED,
    payload,
  };
}

export function getProjectRejected(error) {
  return {
    type: GET_PROJECT_REJECTED,
    error,
  };
}

export function getPredictionPending() {
  return {
    type: GET_PREDICTION_PENDING,
  };
}

export function getPredictionFulfilled(payload) {
  return {
    type: GET_PREDICTION_FULFILLED,
    payload,
  };
}

export function getPredictionRejected(error) {
  return {
    type: GET_PREDICTION_REJECTED,
    error,
  };
}

export function saveProjectPending() {
  return {
    type: SAVE_PROJECT_PENDING,
  };
}

export function saveProjectFulfilled(payload) {
  return {
    type: SAVE_PROJECT_FULFILLED,
    payload,
  };
}

export function saveProjectRejected(error) {
  return {
    type: SAVE_PROJECT_REJECTED,
    error,
  };
}

export function selectToolEdit() {
  return {
    type: SELECT_TOOL_EDIT,
  };
}

export function unselectAll() {
  return {
    type: UNSELECT_ALL,
  };
}

export function setProperties(properties) {
  return {
    type: SET_PROPERTIES,
    properties,
  };
}

export function remove() {
  return {
    type: REMOVE,
  };
}

export function undo() {
  return {
    type: UNDO,
  };
}

export function rollback() {
  return {
    type: ROLLBACK,
  };
}

export function setProjectProperties(properties) {
  return {
    type: SET_PROJECT_PROPERTIES,
    properties,
  };
}

export function enableScaling() {
  return function (dispatch, getState) {
    const enableScalingAction = { type: ENABLE_SCALING };
    const state = getState()['react-planner'];
    const selectedAnnotationsExist = getSelectedAnnotationsSize(state) > 0;

    batch(() => {
      selectedAnnotationsExist && dispatch(unselectAll());
      dispatch(enableScalingAction);
    });
  };
}

export function disableScaling() {
  return {
    type: DISABLE_SCALING,
  };
}

export function removeScalingLines() {
  return {
    type: REMOVE_SCALING_LINES,
  };
}

export function clearScaleDrawing() {
  return {
    type: CLEAR_SCALE_DRAWING,
  };
}

export function setScaleToolProperties(properties) {
  return {
    type: SET_SCALE_TOOL_PROPERTIES,
    payload: properties,
  };
}

export function setSceneProperties(properties) {
  return {
    type: SET_SCENE_PROPERTIES,
    payload: properties,
  };
}

export function setProjectHashCode() {
  return { type: SET_PROJECT_HASH_CODE };
}

export function initCatalog(catalog) {
  return {
    type: INIT_CATALOG,
    catalog,
  };
}

export function toggleCatalogToolbar() {
  return {
    type: TOGGLE_CATALOG_TOOLBAR,
  };
}

export function toggleAutoLabellingFeedback() {
  return {
    type: TOGGLE_AUTOLABELLING_FEEDBACK,
  };
}

export function toggleSnap(mask) {
  return {
    type: TOGGLE_SNAP,
    mask,
  };
}

export function toggleShowSnapElements(mask) {
  return {
    type: TOGGLE_SHOW_SNAP_ELEMENTS,
  };
}

export function throwError(error) {
  return {
    type: THROW_ERROR,
    error,
  };
}

export function throwWarning(warning) {
  return {
    type: THROW_WARNING,
    warning,
  };
}

export function copyProperties(properties) {
  return {
    type: COPY_PROPERTIES,
    properties,
  };
}

export function pasteProperties() {
  return {
    type: PASTE_PROPERTIES,
  };
}

export function pushLastSelectedCatalogElementToHistory(element) {
  return {
    type: PUSH_LAST_SELECTED_CATALOG_ELEMENT_TO_HISTORY,
    element,
  };
}

export function setAlterateState(payload) {
  return {
    type: ALTERATE_STATE,
    payload,
  };
}

export function setCtrlKeyActive(payload) {
  return {
    type: SET_CTRL_KEY_ACTIVE,
    payload,
  };
}

export function setSceneDimensions(payload) {
  return {
    type: SET_SCENE_DIMENSIONS,
    payload,
  };
}

export function setBackgroundDimensions({ width, height }) {
  return {
    type: SET_BACKGROUND_DIMENSIONS,
    payload: { width, height },
  };
}

export function setBackgroundRotation({ rotation }) {
  return {
    type: SET_BACKGROUND_ROTATION,
    payload: { rotation },
  };
}

export function setBackgroundShift({ shift }) {
  return {
    type: SET_BACKGROUND_SHIFT,
    payload: { shift },
  };
}

export function setModeActionCreator(mode) {
  return {
    type: SET_MODE,
    mode,
  };
}

export function setShowBackgroundOnly(payload) {
  return {
    type: SET_SHOW_BACKGROUND_ONLY,
    payload,
  };
}

export function setMode(mode) {
  return function (dispatch, getState) {
    const state = getState()['react-planner'];
    const selectedAnnotationsExist = getSelectedAnnotationsSize(state) > 0;
    const isScaleModeActive = isScaling(state);
    const setModeAction = setModeActionCreator(mode);
    batch(() => {
      isScaleModeActive && dispatch(disableScaling());
      dispatch(setModeAction);
      selectedAnnotationsExist && dispatch(unselectAll());
    });
  };
}

export function setHighlightedError(errorObjectId) {
  return {
    type: SET_HIGHLIGHTED_ERROR,
    payload: errorObjectId,
  };
}

export function setValidationErrors(errors) {
  return {
    type: SET_VALIDATION_ERRORS,
    payload: errors,
  };
}

export function setAnnotationFinished(payload) {
  return {
    type: SET_ANNOTATION_FINISHED,
    payload,
  };
}

export function setMustImportAnnotations(payload) {
  return {
    type: SET_MUST_IMPORT_ANNOTATIONS,
    payload,
  };
}

export function reGenerateAreas() {
  return {
    type: REGENERATE_AREAS,
    payload: undefined,
  };
}

export function setScaleValidated(payload) {
  return {
    type: SET_SCALE_VALIDATED,
    payload,
  };
}

export function setPlanInfo(plan) {
  return {
    type: SET_PLAN_INFO,
    payload: plan,
  };
}

export function showSnackbar(payload) {
  return {
    type: SHOW_SNACKBAR,
    payload,
  };
}

export function closeSnackbar() {
  return {
    type: CLOSE_SNACKBAR,
    payload: undefined,
  };
}

function parseResponse(response) {
  const scene = response.data;
  return { ...response, data: scene };
}

export function getProjectAsync(planId, { onFulfill, onReject } = { onFulfill: project => {}, onReject: error => {} }) {
  return async function (dispatch) {
    dispatch(getProjectPending());
    try {
      const response = await ProviderRequest.get(ENDPOINTS.ANNOTATION_PLAN(planId));
      const project = parseResponse(response);
      dispatch(getProjectFulfilled(project));
      onFulfill(project);
      return project;
    } catch (error) {
      dispatch(getProjectRejected(error));
      onReject(error);
      throw error;
    }
  };
}

export function getPredictionAsync(
  planId,
  { onFulfill, onReject } = { onFulfill: project => {}, onReject: error => {} }
) {
  let stillThereTimer;

  return async function (dispatch) {
    dispatch(getPredictionPending());

    dispatch(
      showSnackbar({
        message: 'Auto-labelling in progress: This could take a while...',
        severity: 'info',
      })
    );
    stillThereTimer = setTimeout(() => {
      dispatch(
        showSnackbar({
          message: 'Auto-labelling: Still working on it...',
          severity: 'info',
        })
      );
    }, STILL_THERE_MS);

    try {
      const prediction: Prediction = await getLabellingPrediction(planId);
      clearTimeout(stillThereTimer);

      dispatch(getPredictionFulfilled(prediction));
      dispatch(
        showSnackbar({
          message: 'Auto-labelling finished successfully',
          severity: 'success',
          duration: 3000,
        })
      );
      dispatch(toggleAutoLabellingFeedback());
      onFulfill(prediction);
      return prediction;
    } catch (error) {
      clearTimeout(stillThereTimer);

      dispatch(
        showSnackbar({
          message: 'Error performing auto-labelling, Tech has been notified',
          severity: 'error',
          duration: 3000,
        })
      );

      dispatch(getPredictionRejected(error));
      onReject(error);
      throw error;
    }
  };
}

const getSceneWithCleanedAreas = (scene, selectedLayer) => {
  const cleanedScene = Object.entries(scene.layers[selectedLayer].areas).reduce((accum, [id, area]) => {
    const { isScaleArea, ...rest } = area as Area;
    accum.layers[selectedLayer].areas[id] = rest;
    return accum;
  }, scene);

  return cleanedScene;
};
const getPreprocessedScene = originalState => {
  let state = cloneDeep(originalState); // As immer forbids to directly modify this
  const selectedLayer = state.scene.selectedLayer;
  state = Project.unselectAll(state).updatedState;
  state = Project.removeScalingLines(state).updatedState;
  state = Layer.removeZeroLengthLines(state, selectedLayer).updatedState;
  state = Layer.removeOrphanLinesAndVertices(state, selectedLayer).updatedState;
  const scene = state.scene;
  const cleanedScene = getSceneWithCleanedAreas(scene, selectedLayer);
  return cleanedScene;
};

export async function savePlan({ planId, state, validated = undefined }) {
  const scene = getPreprocessedScene(state);
  const response = await ProviderRequest.put(ENDPOINTS.ANNOTATION_PLAN(planId, { validated: validated }), scene);
  return parseResponse(response);
}

export function onSaveProjectSuccessfull(project) {
  return function (dispatch) {
    const annotationFinished = Boolean(project?.annotation_finished);
    if (project.errors?.length > 0) {
      dispatch(
        showSnackbar({
          message: 'Project saved but some layout errors where detected, please check them.',
          severity: 'warning',
          duration: 3000,
        })
      );
    } else {
      const message = annotationFinished
        ? 'Project saved and labelled successfully. You can go to classification step.'
        : 'Project saved';
      dispatch(showSnackbar({ message, severity: 'success', duration: null }));
    }
    dispatch(setValidationErrors(project.errors || []));
    dispatch(setAnnotationFinished(annotationFinished));
    dispatch(setProjectHashCode());
  };
}

export function saveProjectAsync({ planId, state, validated }, { onFulfill, onReject }) {
  return async function (dispatch) {
    dispatch(saveProjectPending());
    try {
      const project = await savePlan({ planId, state, validated });
      const currentScaleValidated = state.scaleValidated;
      const projectScaleValidated = Boolean(project?.data?.scale);
      const shouldSetScaleValidated = currentScaleValidated !== projectScaleValidated;

      batch(() => {
        dispatch(saveProjectFulfilled(project));
        shouldSetScaleValidated && dispatch(setScaleValidated(projectScaleValidated));
        onFulfill(project);
      });
    } catch (error) {
      dispatch(saveProjectRejected(error));
      onReject(error);
    }
  };
}

export function saveScale({ planId, scale, stateExtractor, withScaleRatio = false }, { onFulfill, onReject }) {
  return async function (dispatch, getState) {
    try {
      dispatch(planActions.setPlanScale(scale));

      // Set new scale and save it on BE to ensure everything is fine
      dispatch(saveProjectPending());

      const stateWithoutScaleRatio = {
        ...getState()['react-planner'],
        scene: {
          ...getState()['react-planner'].scene,
          paperFormat: '',
          scaleRatio: null,
        },
      };
      // Resetting scale ratio values
      const state = withScaleRatio ? getState()['react-planner'] : stateWithoutScaleRatio;

      let project = await savePlan({ planId, state });
      dispatch(saveProjectFulfilled(project));
      dispatch(setScaleValidated(true));

      // Save the plan to ensure we store the last version with updated lines
      dispatch(saveProjectPending());
      project = await savePlan({ planId, state });
      dispatch(saveProjectFulfilled(project));

      onFulfill(project);
    } catch (error) {
      dispatch(saveProjectRejected(error));
      onReject(error);
    }
  };
}

// @TODO: Probably this could be in plan-actions, migrate there
export function getPlanInfoAsync(planId, { onFulfill, onReject } = { onFulfill: plan => {}, onReject: error => {} }) {
  return function (dispatch) {
    return ProviderRequest.get(ENDPOINTS.PLAN_BY_ID(planId)).then(
      response => {
        const plan = parseResponse(response);
        dispatch(setPlanInfo(plan));
        onFulfill(plan);
        return plan;
      },
      error => {
        onReject(error);
        throw error;
      }
    );
  };
}
