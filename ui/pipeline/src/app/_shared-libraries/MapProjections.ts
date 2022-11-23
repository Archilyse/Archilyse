import { register as RegisterProjectionsInOL } from 'ol/proj/proj4';
import proj4 from 'proj4';

export function addProjection(projectionName, projectionWktString) {
  proj4.defs(projectionName, projectionWktString);
}

export function registerProjections(projections) {
  try {
    Object.entries(projections).forEach(([projectionName, projectionWktString]: [string, string]) => {
      addProjection(projectionName, projectionWktString);
    });
    RegisterProjectionsInOL(proj4);
  } catch (error) {
    throw new Error(`Error registering projections ${error}`);
  }
}
