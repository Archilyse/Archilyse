// https://stackoverflow.com/questions/33444711/js-object-has-property-deep-check

import { ApiService } from '../_services/api.service';

export function hasOwnNestedProperty(object, propertyPath) {
  if (!propertyPath) {
    return false;
  }

  const properties = propertyPath.split('.');

  // tslint:disable-next-line:no-this-assignment
  let obj = object;

  for (let i = 0; i < properties.length; i += 1) {
    const prop = properties[i];

    if (!obj || !obj.hasOwnProperty(prop)) {
      return false;
    }

    obj = obj[prop];
  }

  return true;
}

export const isSiteSimulatedAlready = async (apiService: ApiService, planId: string) => {
  const siteId = (await apiService.getPlanData(planId)).site_id;
  const siteData = await apiService.getSite(siteId);
  return siteData.full_slam_results === 'SUCCESS' && siteData.heatmaps_qa_complete === true;
};

export const shouldSave = async (apiService: ApiService, planId: string) => {
  if (await isSiteSimulatedAlready(apiService, planId)) {
    return window.confirm('Please note that this site is already simulated. Are you sure you want to change it?');
  }
  return true;
};
