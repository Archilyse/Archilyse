import { Plan } from '../class/export';
import {
  FETCH_FLOOR_SCALES_FULFILLED,
  FETCH_FLOOR_SCALES_PENDING,
  FETCH_FLOORPLAN_FULFILLED,
  FETCH_SITE_CLASSIFICATION_FULFILLED,
  FETCH_SITE_STRUCTURE_FULFILLED,
  REQUEST_STATUS_BY_ACTION,
  SET_FLOORPLAN_DIMENSIONS,
  SET_PLAN_SCALE,
} from '../constants';
import RequestStatus from '../class/request-status';

export default (state, action) => {
  switch (action.type) {
    case FETCH_FLOORPLAN_FULFILLED:
      return Plan.createFloorplanUrl(state, action).updatedState;
    case SET_PLAN_SCALE:
      return Plan.setScale(state, action).updatedState;
    case FETCH_SITE_CLASSIFICATION_FULFILLED:
      return Plan.setAvailableAreaTypes(state, action).updatedState;
    case FETCH_SITE_STRUCTURE_FULFILLED:
      return Plan.setSiteStructure(state, action).updatedState;
    case FETCH_FLOOR_SCALES_PENDING:
      return RequestStatus.setPending(state, REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES);
    case FETCH_FLOOR_SCALES_FULFILLED: {
      const updatedState = Plan.setFloorScales(state, action).updatedState;
      return RequestStatus.setFulfilled(updatedState, REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES);
    }
    case SET_FLOORPLAN_DIMENSIONS:
      return Plan.setFloorplanDimensions(state, action.payload).updatedState;

    default:
      return state;
  }
};
