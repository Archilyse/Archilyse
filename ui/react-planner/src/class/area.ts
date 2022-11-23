import { Feature, Polygon } from 'geojson';
import { Area as AreaType, UpdatedStateObject } from '../types';
import * as GeometryUtils from '../utils/geometry';
import IDBroker from '../utils/id-broker';
import NameGenerator from '../utils/name-generator';

import Layer from './layer';

class Area {
  static add(
    state,
    layerID,
    type,
    coords,
    catalog,
    areaType,
    isScaleArea = false
  ): UpdatedStateObject & { area: AreaType } {
    const areaID = IDBroker.acquireID();

    const area = catalog.factoryElement(type, {
      id: areaID,
      name: NameGenerator.generateName('areas', catalog.elements[type].info.title),
      type,
      prototype: 'areas',
      coords: coords,
      areaType,
    });
    area.isScaleArea = isScaleArea;
    state.scene.layers[layerID].areas[areaID] = area;

    return { updatedState: state, area };
  }

  static getAreaIntersectingCoordinates(scene, x, y): Feature<Polygon> | null {
    const selectedLayerID = scene.selectedLayer;
    const areas = scene.layers[selectedLayerID].areas;

    for (const area of Object.values(areas)) {
      const AreaPolygon = GeometryUtils.getAreaPolygon(area);
      const ItemPoint = GeometryUtils.getPoint(x, y);
      const intersect = GeometryUtils.booleanIntersects(ItemPoint, AreaPolygon);
      if (intersect) {
        return AreaPolygon;
      }
    }
    return null;
  }

  static select(state, layerID, areaID, options = { unselectAllBefore: true }): UpdatedStateObject {
    if (options.unselectAllBefore) {
      state = Layer.select(state, layerID).updatedState;
    }
    state = Layer.selectElement(state, layerID, 'areas', areaID).updatedState;

    return { updatedState: state };
  }

  static remove(state, layerID, areaID): UpdatedStateObject {
    const area = state.scene.layers[layerID].areas[areaID];

    if (area.selected === true) state = this.unselect(state, layerID, areaID).updatedState;

    delete state.scene.layers[layerID].areas[areaID];

    return { updatedState: state };
  }

  static unselect(state, layerID, areaID): UpdatedStateObject {
    state = Layer.unselect(state, layerID, 'areas', areaID).updatedState;

    return { updatedState: state };
  }

  static setProperties(state, layerID, areaID, properties): UpdatedStateObject {
    state.scene.layers[layerID].areas[areaID].properties = {
      ...state.scene.layers[layerID].areas[areaID].properties,
      ...properties,
    };

    return { updatedState: state };
  }

  static setJsProperties(state, layerID, areaID, properties): UpdatedStateObject {
    return this.setProperties(state, layerID, areaID, properties);
  }

  static updateProperties(state, layerID, areaID, properties): UpdatedStateObject {
    const propertiesEntries = Object.entries(properties) as any;

    propertiesEntries.forEach(([k, v]) => {
      const lineHasProperty = state.scene.layers[layerID].areas[areaID].properties.hasOwnProperty(k);
      if (lineHasProperty) {
        state.scene.layers[layerID].areas[areaID].properties = {
          ...state.scene.layers[layerID].areas[areaID].properties,
          [k]: v,
        };
      }
    });
    return { updatedState: state };
  }

  static updateJsProperties(state, layerID, areaID, properties): UpdatedStateObject {
    return this.updateProperties(state, layerID, areaID, properties);
  }
}

export { Area as default };
