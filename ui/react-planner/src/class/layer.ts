import { Feature, MultiPolygon, Polygon } from 'geojson';
import * as GeometryUtils from '../utils/geometry';
import { SeparatorsType } from '../constants';
import {
  ElementPrototype,
  Layer as LayerType,
  Line as LineType,
  State as StateType,
  UpdatedStateObject,
  Vertex as VertexType,
} from '../types';
import getFastStateObject from '../utils/get-fast-state-object';
import Project from './project';
import Line from './line';
import Hole from './hole';
import Vertex from './vertex';
import Area from './area';
import Item from './item';

const getSelectedElements = (
  state: StateType,
  layerID: 'layer-1',
  elementPrototype: ElementPrototype['type']
): any[] => {
  return state.scene.layers[layerID].selected[elementPrototype]
    ? Array.from(state.scene.layers[layerID].selected[elementPrototype])
    : [];
};
const calculateOuterBboxPolygon = (linesMultiPolygon): Feature<Polygon | MultiPolygon> => {
  const bbox = GeometryUtils.getBoundingBox(linesMultiPolygon);
  const bboxPolygon = GeometryUtils.getPolygonFromBoundingBox(bbox);
  return GeometryUtils.scaleFeature(bboxPolygon) as Feature<Polygon | MultiPolygon>;
};

const getLinesMultiPolygon = (state, layerID, options = { detectScaleAreasOnly: false }) => {
  const linePolygonCoords = [];

  const allLines: LineType[] = Object.values(state.scene.layers[layerID].lines);
  for (let i = 0; i < allLines.length; i++) {
    const line = allLines[i];

    if (options.detectScaleAreasOnly) {
      if (line.type !== SeparatorsType.SCALE_TOOL) {
        continue;
      }
    }

    const linePolygon = Line.getPolygon(line);
    if (linePolygon) {
      const preprocessedPolygonCoords = GeometryUtils.preprocessFeatureForUnion(linePolygon);
      linePolygonCoords.push(preprocessedPolygonCoords);
    }
  }
  if (!linePolygonCoords.length) return null; // No areas

  return GeometryUtils.joinPolygons(linePolygonCoords);
};

const getAreasMultiPolygon = areasWithBBboxPolygon => {
  if (!areasWithBBboxPolygon) return null;
  const biggestPolygon = GeometryUtils.findBiggestPolygonInMultiPolygon(areasWithBBboxPolygon);
  if (!biggestPolygon) return null;
  const difference = GeometryUtils.getDifference(areasWithBBboxPolygon, biggestPolygon);
  if (difference.geometry.type === 'Polygon') {
    return GeometryUtils.getMultiPolygon([difference.geometry.coordinates]);
  }
  return difference;
};

class Layer {
  static select(state, layerID): UpdatedStateObject {
    if (!state.alterate && !state.ctrlActive) state = Project.unselectAll(state).updatedState;

    state.scene.selectedLayer = layerID;
    return { updatedState: state };
  }

  static selectElement(state, layerID, elementPrototype, elementID): UpdatedStateObject {
    const selectedElems = getSelectedElements(state, layerID, elementPrototype);
    if (!selectedElems.includes(elementID)) {
      selectedElems.push(elementID);
    }

    state.scene.layers[layerID][elementPrototype][elementID].selected = true;
    state.scene.layers[layerID].selected[elementPrototype] = selectedElems;

    return { updatedState: state };
  }

  static unselect(state, layerID, elementPrototype, elementID): UpdatedStateObject {
    let selectedElems = getSelectedElements(state, layerID, elementPrototype);
    selectedElems = selectedElems.filter(elId => elId !== elementID);

    state.scene.layers[layerID][elementPrototype][elementID].selected = false;
    state.scene.layers[layerID].selected[elementPrototype] = selectedElems;

    return { updatedState: state };
  }

  static unselectAll(state, layerID): UpdatedStateObject {
    const { lines = [], holes = [], items = [], areas = [], vertices = [] } = state.scene.layers[layerID].selected;

    vertices.forEach(vertexId => {
      state = Vertex.unselect(state, layerID, vertexId).updatedState;
    });
    lines.forEach(lineId => {
      state = Line.unselect(state, layerID, lineId).updatedState;
    });
    holes.forEach(holeId => {
      state = Hole.unselect(state, layerID, holeId).updatedState;
    });
    items.forEach(itemId => {
      state = Item.unselect(state, layerID, itemId).updatedState;
    });
    areas.forEach(areaId => {
      state = Area.unselect(state, layerID, areaId).updatedState;
    });

    return { updatedState: state };
  }

  static removeElement(state, layerID, elementPrototype, elementID): UpdatedStateObject {
    const { [elementID]: toBeDeleted, ...restElements } = state.scene.layers[layerID][elementPrototype];
    state.scene.layers[layerID][elementPrototype] = restElements;

    return { updatedState: state };
  }

  static addAreasFromCoords(state, layerID, multiPolygonCoords, isScaleArea): UpdatedStateObject {
    multiPolygonCoords.forEach(coords => {
      state = Area.add(state, layerID, 'area', coords, state.catalog, null, isScaleArea).updatedState;
    });
    return { updatedState: state };
  }

  /*
    The algorithm here is the same as in space_maker in the BE:

    - Create a multipolygon with all the polygons of the lines
    - Create the bbox of all this polygons
    - Scale it so is the biggest polygon
    - Get the difference of the bbox and this lines multipolygons: Now we have our areas and the bbbox
    - Remove the bbox
    - Profit!
  */
  static detectAndUpdateAreas(state, layerID, options = { detectScaleAreasOnly: false }): UpdatedStateObject {
    const fastState = getFastStateObject(state);
    const lines = Object.values(fastState.scene.layers[layerID].lines);
    if (lines.length < 2) return { updatedState: state };
    // If we are on scaling, we only want to add the new scale area, not remove the old ones
    if (!options.detectScaleAreasOnly) {
      Object.keys(fastState.scene.layers[layerID].areas).forEach(areaID => {
        state = Area.remove(state, layerID, areaID).updatedState;
      });
    }

    // Get all lines ("separators") and the outer bbox of them
    const linesMultiPolygon = getLinesMultiPolygon(fastState, layerID, options);
    const outerBBoxPolygon = calculateOuterBboxPolygon(linesMultiPolygon);

    // Get the multipolygon containing the areas + the polygon of the outer bbox
    const areasWithBBboxPolygon = GeometryUtils.getDifference(outerBBoxPolygon, linesMultiPolygon);

    // Get the final areas by substracting the big outer bbox polygon
    const areasMultiPolygon = getAreasMultiPolygon(areasWithBBboxPolygon);
    if (!areasMultiPolygon) return { updatedState: state };

    const coords = GeometryUtils.getFeatureCoords(areasMultiPolygon);

    const isScaleArea = options.detectScaleAreasOnly;
    state = this.addAreasFromCoords(state, layerID, coords, isScaleArea).updatedState;
    return {
      updatedState: state,
    };
  }

  static removeZeroLengthLines(state, layerID): UpdatedStateObject {
    const lines: LineType[] = Object.values(state.scene.layers[layerID].lines);
    const updatedState = lines.reduce((newState, line) => {
      const [firstVertexId, secondVertexId] = line.vertices;
      const allVertices = newState.scene.layers[layerID].vertices;
      const v0 = allVertices[firstVertexId];
      const v1 = allVertices[secondVertexId];

      if (GeometryUtils.lineHasZeroLength(v0, v1)) {
        newState = Line.remove(newState, layerID, line.id).updatedState;
      }
      return newState;
    }, state);

    return { updatedState };
  }

  // Removes Orphan Vertices and non existent lines referenced on vertices
  static removeOrphanLinesAndVertices(state, layerID): UpdatedStateObject {
    const vertices: VertexType[] = Object.values(state.scene.layers[layerID].vertices);
    const lineIdsOnVertices = vertices.map(({ lines }) => lines).flat();
    const existingLines = Object.keys(state.scene.layers[layerID].lines);
    const orphanLines = lineIdsOnVertices.filter(currentLineId => {
      const lineExists = existingLines.includes(currentLineId);
      return !lineExists;
    });

    // here we remove the orphan vertices and orphan lines references
    const newVertices = vertices.reduce((acc, vertex) => {
      const newAcc = acc;
      const id = vertex.id;
      const orphanLineId = orphanLines.find(lineId => vertex.lines.includes(lineId));
      if (orphanLineId) {
        const filteredLines = vertex.lines.filter(lineId => lineId !== orphanLineId);
        vertex = {
          ...vertex,
          lines: filteredLines,
        };
      }
      const vertexIsOrphan = vertex.lines.length === 0;
      if (!vertexIsOrphan) {
        newAcc[id] = vertex;
      }
      return newAcc;
    }, {});

    state.scene.layers[layerID].vertices = newVertices;

    return { updatedState: state };
  }

  static mergeEqualsVertices(state, layerID, vertexID): UpdatedStateObject {
    //1. find vertices to remove
    const vertex = state.scene.layers[layerID].vertices[vertexID];

    const layerVertices: LayerType['vertices'] = state.scene.layers[layerID].vertices;
    const doubleVertices = Object.values(layerVertices).filter((v: VertexType) => {
      return v.id !== vertexID && GeometryUtils.samePoints(vertex, v);
    });

    if (doubleVertices.length === 0) return { updatedState: state };

    doubleVertices.forEach(doubleVertex => {
      const reduced = doubleVertex.lines.reduce((reducedState, lineID) => {
        reducedState = reducedState.updateIn(['scene', 'layers', layerID, 'lines', lineID, 'vertices'], vertices => {
          if (vertices) {
            return vertices.map(v => (v === doubleVertex.id ? vertexID : v));
          }
        });
        reducedState = Vertex.addElement(reducedState, layerID, vertexID, 'lines', lineID).updatedState;

        return reducedState;
      }, state);

      state = Vertex.remove(reduced, layerID, doubleVertex.id).updatedState;
    });

    return { updatedState: state };
  }

  static setPropertiesOnSelected(state, layerID, properties): UpdatedStateObject {
    const selected = state.scene.layers[layerID].selected;

    selected.lines.forEach(lineID => (state = Line.setProperties(state, layerID, lineID, properties).updatedState));
    selected.holes.forEach(holeID => (state = Hole.setProperties(state, layerID, holeID, properties).updatedState));
    selected.areas.forEach(areaID => (state = Area.setProperties(state, layerID, areaID, properties).updatedState));
    selected.items.forEach(itemID => (state = Item.setProperties(state, layerID, itemID, properties).updatedState));

    return { updatedState: state };
  }

  static updatePropertiesOnSelected(state, layerID, properties): UpdatedStateObject {
    const selected = state.scene.layers[layerID].selected;

    selected.lines.forEach(lineID => (state = Line.updateProperties(state, layerID, lineID, properties).updatedState));
    selected.holes.forEach(holeID => (state = Hole.updateProperties(state, layerID, holeID, properties).updatedState));
    selected.areas.forEach(areaID => (state = Area.updateProperties(state, layerID, areaID, properties).updatedState));
    selected.items.forEach(itemID => (state = Item.updateProperties(state, layerID, itemID, properties).updatedState));

    return { updatedState: state };
  }

  static setAttributesOnSelected(state, layerID, attributes): UpdatedStateObject {
    const selected = state.scene.layers[layerID].selected;

    selected.lines.forEach(lineID => (state = Line.setAttributes(state, layerID, lineID, attributes).updatedState));
    selected.holes.forEach(holeID => (state = Hole.setAttributes(state, layerID, holeID, attributes).updatedState));
    selected.items.forEach(itemID => (state = Item.setAttributes(state, layerID, itemID, attributes).updatedState));

    return { updatedState: state };
  }
}

export { Layer as default };
