import { ProviderRequest } from '../providers';
import {
  ENDPOINTS as E,
  FETCH_FLOOR_SCALES_FULFILLED,
  FETCH_FLOOR_SCALES_PENDING,
  FETCH_FLOORPLAN_FULFILLED,
  FETCH_FLOORPLAN_PENDING,
  FETCH_FLOORPLAN_REJECTED,
  FETCH_SITE_CLASSIFICATION_FULFILLED,
  FETCH_SITE_CLASSIFICATION_REJECTED,
  FETCH_SITE_STRUCTURE_FULFILLED,
  FETCH_SITE_STRUCTURE_REJECTED,
  SET_FLOORPLAN_DIMENSIONS,
  SET_PLAN_SCALE,
} from '../constants';
import { FloorScale } from '../types';

export function setPlanScale(scale) {
  return {
    type: SET_PLAN_SCALE,
    payload: scale,
  };
}

export function pendingFloorplan() {
  return {
    type: FETCH_FLOORPLAN_PENDING,
  };
}

export function fulfilledFloorplan(image) {
  return {
    type: FETCH_FLOORPLAN_FULFILLED,
    payload: image,
  };
}

export function rejectedFloorplan(error) {
  return {
    type: FETCH_FLOORPLAN_REJECTED,
    error,
  };
}

export function fulfilledClassification(success) {
  return {
    type: FETCH_SITE_CLASSIFICATION_FULFILLED,
    payload: success,
  };
}

export function rejectedClassification(error) {
  return {
    type: FETCH_SITE_CLASSIFICATION_REJECTED,
    error,
  };
}

export function fullfilledSiteStructure(structure) {
  return {
    type: FETCH_SITE_STRUCTURE_FULFILLED,
    payload: structure,
  };
}

export function rejectedSiteStructure(error) {
  return {
    type: FETCH_SITE_STRUCTURE_REJECTED,
    error,
  };
}

export function pendingFloorScales() {
  return {
    type: FETCH_FLOOR_SCALES_PENDING,
  };
}

export function fulfilledFloorScales(floorScales) {
  return {
    type: FETCH_FLOOR_SCALES_FULFILLED,
    payload: floorScales,
  };
}

export function setFloorplanDimensions({ width, height }) {
  return {
    type: SET_FLOORPLAN_DIMENSIONS,
    payload: { width, height },
  };
}

export function fetchFloorplan(planId) {
  return function (dispatch) {
    dispatch(pendingFloorplan);
    return ProviderRequest.get(E.FLOORPLAN_IMG_PLAN(planId), { responseType: 'blob' }).then(
      image => ({ payload: image }),
      error => dispatch(rejectedFloorplan(error))
    );
  };
}

async function fetchAreaTypes(plan) {
  const site = await ProviderRequest.get(E.SITE_BY_ID(plan.site_id));
  return ProviderRequest.get(E.CLASSIFICATION_SCHEME(site.classification_scheme));
}

export function fetchAvailableAreaTypes(plan) {
  return function (dispatch) {
    return fetchAreaTypes(plan).then(
      success => dispatch(fulfilledClassification(success)),
      error => dispatch(rejectedClassification(error))
    );
  };
}

export function fetchSiteStructure(plan) {
  return function (dispatch) {
    return ProviderRequest.get(E.SITE_STRUCTURE(plan.site_id)).then(
      rawStructure => dispatch(fullfilledSiteStructure({ rawStructure, planId: plan.id })),
      error => dispatch(rejectedSiteStructure(error))
    );
  };
}

export function fetchFloorScales(planId, siteStructure) {
  return async function (dispatch) {
    dispatch(pendingFloorScales());

    const scaleRequests = siteStructure.floors.map(async floor => {
      if (Number(floor.plan_id) === Number(planId)) return null;
      try {
        const response = await ProviderRequest.get(E.ANNOTATION_PLAN(floor.plan_id, { validated: false }));
        return {
          floorNumber: floor.floor_number,
          planId: floor.plan_id,
          scale: response?.data?.scale,
        };
      } catch (error) {
        console.log(`Error getting scale for plan ${floor.plan_id}: ${error}`);
        return { floorNumber: floor.floor_number, planId: floor.plan_id, scale: 0, error };
      }
    });
    const responses: FloorScale[] = await Promise.all(scaleRequests);
    const scales = responses.filter(response => response);

    dispatch(fulfilledFloorScales(scales));
  };
}
