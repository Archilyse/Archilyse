import produce from 'immer';
import {
  AREA_ACTIONS,
  COPY_PASTE_ACTIONS,
  HOLE_ACTIONS,
  ITEMS_ACTIONS,
  LINE_ACTIONS,
  PLAN_ACTIONS,
  PROJECT_ACTIONS,
  RECTANGLE_TOOL_ACTIONS,
  SCENE_ACTIONS,
  VERTEX_ACTIONS,
  VIEWER2D_ACTIONS,
} from '../constants';

import { State } from '../models';
import {
  ReactPlannerAreasReducer,
  ReactPlannerCopyPasteReducer,
  ReactPlannerHolesReducer,
  ReactPlannerItemsReducer,
  ReactPlannerLinesReducer,
  ReactPlannerPlanReducer,
  ReactPlannerProjectReducer,
  ReactPlannerRectangleSelectToolReducer,
  ReactPlannerSceneReducer,
  ReactPlannerVerticesReducer,
  ReactPlannerViewer2dReducer,
} from './export';

export const initialState = new State();

export default function appReducer(baseState, action) {
  return produce(baseState, state => {
    if (action.type === 'SET_NEW' && action.data) return new State(action.data['react-planner']);
    if (PROJECT_ACTIONS[action.type]) return ReactPlannerProjectReducer(state, action);
    if (VIEWER2D_ACTIONS[action.type]) return ReactPlannerViewer2dReducer(state, action);
    if (ITEMS_ACTIONS[action.type]) return ReactPlannerItemsReducer(state, action);
    if (HOLE_ACTIONS[action.type]) return ReactPlannerHolesReducer(state, action);
    if (LINE_ACTIONS[action.type]) return ReactPlannerLinesReducer(state, action);
    if (AREA_ACTIONS[action.type]) return ReactPlannerAreasReducer(state, action);
    if (PLAN_ACTIONS[action.type]) return ReactPlannerPlanReducer(state, action);
    if (SCENE_ACTIONS[action.type]) return ReactPlannerSceneReducer(state, action);
    if (VERTEX_ACTIONS[action.type]) return ReactPlannerVerticesReducer(state, action);
    if (COPY_PASTE_ACTIONS[action.type]) return ReactPlannerCopyPasteReducer(state, action);
    if (RECTANGLE_TOOL_ACTIONS[action.type]) return ReactPlannerRectangleSelectToolReducer(state, action);
    return state || initialState;
  });
}
