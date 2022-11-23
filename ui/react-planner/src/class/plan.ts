import { SiteStructure as FullSiteStructure } from 'archilyse-ui-components';
import { SiteStructure } from '../types';

const getHumanAreaTypeName = areaName => {
  const prefixes = ['AreaType.', 'PostDynamicAreaTypes.'];
  return prefixes.reduce((res, prefix) => res.replace(prefix, ''), areaName);
};

function getSiteStructureForCurrentPlan(rawStructure: FullSiteStructure, planId: number): SiteStructure {
  const currentBuilding = rawStructure.buildings.find(building => {
    return Object.values(building.floors || {}).some(floor => Number(floor.plan_id) === Number(planId));
  });

  return {
    client_site_id: rawStructure.client_site_id,
    site: { name: rawStructure.name, id: rawStructure.id },
    building: { street: currentBuilding?.street, housenumber: currentBuilding?.housenumber, id: currentBuilding?.id },
    floors: currentBuilding ? Object.values(currentBuilding.floors) : [],
    planId,
  };
}

class Plan {
  static createFloorplanUrl(state, action) {
    const isBlob = typeof action.payload !== 'string';
    const imgUrl = isBlob ? URL.createObjectURL(action.payload) : action.payload;
    state.floorplanImgUrl = imgUrl;
    return { updatedState: state };
  }
  static setScale(state, action) {
    const planScale = action.payload;
    state.scene.scale = planScale;
    return { updatedState: state };
  }

  static setFloorplanDimensions(state, { width, height }) {
    state.floorplanDimensions = {
      width,
      height,
    };
    return { updatedState: state };
  }

  static setAvailableAreaTypes(state, action) {
    const areaTypeStructure = action.payload;
    const areaTypes = ['NOT_DEFINED'];
    Object.keys(areaTypeStructure).forEach(key => {
      const value = areaTypeStructure[key];
      if (!value.children || !value.children.length) {
        areaTypes.push(getHumanAreaTypeName(key));
      }
    });

    const finalAreaTypes = {};
    areaTypes
      .sort((a: any, b: any) => a.order - b.order)
      .forEach(areaType => {
        finalAreaTypes[areaType.toLowerCase()] = areaType;
      });

    state.availableAreaTypes = finalAreaTypes;
    return { updatedState: state };
  }

  static setSiteStructure(state, action) {
    const { rawStructure, planId } = action.payload;
    const structure = getSiteStructureForCurrentPlan(rawStructure, planId);
    state.siteStructure = structure;

    return { updatedState: state };
  }

  static setFloorScales(state, action) {
    const floorScales = action.payload;
    state.floorScales = floorScales;

    return { updatedState: state };
  }
}

export { Plan as default };
