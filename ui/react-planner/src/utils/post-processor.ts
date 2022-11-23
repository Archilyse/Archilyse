import { Feature, MultiPolygon, Polygon, Position } from 'geojson';
import {
  ACCEPTED_NUMBER_OF_COORDINATES,
  ACCEPTED_NUMBER_OF_POLYGON_EDGES,
  GEOJSON_FEATURE_TYPES,
  MODE_DRAWING_LINE,
} from '../constants';
import Line from '../class/line';
import Hole from '../class/hole';
import Vertex from '../class/vertex';
import * as GeometryUtils from './geometry';
import { getSelectedLayer } from './state-utils';

class PostProcessor {
  static hasRepeatedVerticesCoords(line, layer): boolean {
    const allLineVertices = [...line.vertices, ...line.auxVertices];

    const XYCoordsPerVertexID = allLineVertices.reduce((accum, vertexID) => {
      const vertex = layer.vertices[vertexID];
      accum[`${vertex.x}, ${vertex.y}`] = vertexID;
      return accum;
    }, {});
    return allLineVertices.some(vertexID => {
      const vertex = layer.vertices[vertexID];
      const vertexWithSameCoords = XYCoordsPerVertexID[`${vertex.x}, ${vertex.y}`];
      return vertexWithSameCoords && vertexWithSameCoords != vertexID;
    });
  }

  static hasValidCoordinates(coordinates: Position[][]): boolean {
    const polygon = GeometryUtils.createPolygon(coordinates);
    const simplifiedPolygon = GeometryUtils.getSimplifiedPolygon(polygon);
    const [simplifiedCoordinates] = simplifiedPolygon.geometry.coordinates;
    if (simplifiedCoordinates.length === ACCEPTED_NUMBER_OF_COORDINATES) {
      return GeometryUtils.getPolygonEdges(polygon).length === ACCEPTED_NUMBER_OF_POLYGON_EDGES;
    }
    return false;
  }
  static isValid(state, postprocessedLineIDs: string[]) {
    const layer = getSelectedLayer(state.scene);

    return postprocessedLineIDs.every(lineID => {
      const line = layer.lines[lineID];
      const hasCorrectNumberOfVertices = line.vertices.length === 2 && line.auxVertices.length === 4;
      const hasValidCoordinates = this.hasValidCoordinates(line.coordinates);
      return hasCorrectNumberOfVertices && hasValidCoordinates && !this.hasRepeatedVerticesCoords(line, layer);
    });
  }
  static postprocessLine(state, layerID, lineID, intersectingLines) {
    const layer = getSelectedLayer(state.scene);
    const line = layer.lines[lineID];

    const linePolygon = this.removeIntersections(state, lineID, intersectingLines);
    const { vertices, auxVertices, coordinates } = this.extractCoordsAndVerticesFromPolygon(state, lineID, linePolygon);

    vertices.forEach(({ x, y }, index) => {
      state = Line.replaceVertex(state, layerID, lineID, index, x, y, { force: true }).updatedState;
    });

    state = line.auxVertices.reduce(
      (accumulatedState, vertexID) => Vertex.remove(accumulatedState, layerID, vertexID, 'lines', lineID).updatedState,
      state
    );

    const newAuxIds = [];
    for (const { x, y } of auxVertices) {
      const { updatedState, vertex } = Vertex.add(state, layerID, x, y, 'lines', lineID, { force: true });
      newAuxIds.push(vertex.id);
      state = updatedState;
    }

    state = Line.orderMainVertices(state, layerID, lineID).updatedState;
    state.scene.layers[layerID].lines[lineID].auxVertices = newAuxIds;
    state.scene.layers[layerID].lines[lineID].coordinates = coordinates;

    line.holes.forEach(holeID => {
      state = Hole.adjustHolePolygonAfterLineChange(state, layerID, holeID).updatedState;
    });
    return { updatedState: state };
  }

  /*
   * This ensures the line to be postprocessed is "correct" by recreating it
   *  Otherwise, unexpected results may appear (with imported lines via dxf, non postprocessed fixtures..)
   *  Notice we only do this if we are drawing, to avoid an infinite loop as recreateLineShape calls `postprocess` on IDLE mode
   */
  static ensureLineShapeIsCorrect(state, layerID, lineID) {
    if (state.mode === MODE_DRAWING_LINE) {
      const shouldReloadAreas = false;
      state = Line.recreateLineShape(state, layerID, lineID, shouldReloadAreas).updatedState;
    }
    return { updatedState: state };
  }

  static postprocessLines(state, layerID, firstLineID) {
    const processingCounter: Map<string, number> = new Map<string, number>();
    const processingQueue: Array<string> = new Array<string>();
    processingQueue.push(firstLineID);

    while (processingQueue.length > 0) {
      const currentLineID = processingQueue.shift();
      const layer = getSelectedLayer(state.scene);
      const intersectingLines = GeometryUtils.getPostProcessableIntersectingLines(layer, currentLineID);
      if (!processingCounter.has(currentLineID)) {
        processingCounter.set(currentLineID, intersectingLines.length);
      }
      const processingCount = processingCounter.get(currentLineID);
      if (processingCount == 0) continue;

      intersectingLines.forEach(l => processingQueue.push(l.id));

      state = this.ensureLineShapeIsCorrect(state, layerID, currentLineID).updatedState;

      state = this.postprocessLine(state, layerID, currentLineID, intersectingLines).updatedState;

      const updatedProcessingCount = processingCounter.get(currentLineID) - 1;
      processingCounter.set(currentLineID, updatedProcessingCount);
    }

    return { updatedState: state, postprocessedLineIDs: Array.from(processingCounter.keys()) };
  }

  static extractCoordsAndVerticesFromPolygon(state, lineID: string, linePolygon: Feature<Polygon>) {
    /**
     * Returns an object containing new vertices, new auxVertices and updated line coordinates based
     * on the passed line polygon.
     * 1. The updated coordinates correspond to the convex hull of the linePolygon;
     * 2. Each vertex of newly created convex hull, that is on the reference line of the passed line
     * is the main vertex.
     * 3. Every other vertex - excluding the last wrapping vertex, but including the middle-points of
     * shortest convex hull sides are the new auxVertices.
     */
    const layer = getSelectedLayer(state.scene);
    const line = layer.lines[lineID];

    const convexHull = GeometryUtils.getSimplifiedPolygon(linePolygon);
    const layerVertices = layer.vertices;
    const [lv0, lv1] = line.vertices.map(vertexID => layerVertices[vertexID]);
    const mainReferenceLine = { x1: lv0.x, y1: lv0.y, x2: lv1.x, y2: lv1.y };
    const [av0, av1, av2, av3] = line.auxVertices.map(vertexID => layerVertices[vertexID]);
    const auxLines = [
      { x1: av0.x, y1: av0.y, x2: av1.x, y2: av1.y },
      { x1: av2.x, y1: av2.y, x2: av3.x, y2: av3.y },
    ];

    const { vertices, auxVertices } = GeometryUtils.getVerticesFromPolygon(convexHull, mainReferenceLine, auxLines);

    return {
      vertices,
      auxVertices,
      coordinates: convexHull.geometry.coordinates,
    };
  }

  static removeIntersections(state, lineID: string, intersectingLines): Feature<Polygon> {
    const layer = getSelectedLayer(state.scene);
    const line = layer.lines[lineID];
    const coords = line.coordinates;
    const linePolygon = GeometryUtils.createPolygon(coords);

    const outputPolygon = intersectingLines.reduce((accumulator, currentLine) => {
      const lineCoords = currentLine.coordinates;
      const rawPolygon = GeometryUtils.createPolygon(lineCoords);
      const polygon = GeometryUtils.preprocessForOperation(rawPolygon) as Feature<Polygon>;
      const preprocessedAccum = GeometryUtils.preprocessForOperation(accumulator) as Feature<Polygon>;

      const intersection = GeometryUtils.intersect(preprocessedAccum, polygon);
      if (!intersection) return GeometryUtils.toXYCoords(preprocessedAccum);

      let newPolygon = GeometryUtils.getDifference(preprocessedAccum, polygon);
      newPolygon = GeometryUtils.toXYCoords(newPolygon) as Feature<Polygon | MultiPolygon>;
      newPolygon = GeometryUtils.roundFeature(newPolygon);

      // TODO: decide what we should do with line segments that are cut in half by another one. what's
      // happening right now is that only the larger of the two polygons from split up line should be
      // consider for postprocessing.
      if (newPolygon.geometry.type === GEOJSON_FEATURE_TYPES.MULTIPOLYGON) {
        newPolygon = GeometryUtils.findBiggestPolygonInMultiPolygon(newPolygon as Feature<MultiPolygon>);
      }
      const simplifiedPolygon = GeometryUtils.getSimplifiedPolygon(newPolygon as Feature<Polygon>);
      const simplifiedPolygonCoords = simplifiedPolygon.geometry.coordinates;
      return this.hasValidCoordinates(simplifiedPolygonCoords) ? simplifiedPolygon : linePolygon;
    }, linePolygon);

    return outputPolygon;
  }
}

export default PostProcessor;
