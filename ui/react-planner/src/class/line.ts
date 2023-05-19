import { capitalize } from 'archilyse-ui-components';
import * as GeometryUtils from '../utils/geometry';
import * as history from '../utils/history';
import IDBroker from '../utils/id-broker';
import NameGenerator from '../utils/name-generator';
import PostProcessor from '../utils/post-processor';
import * as SnapSceneUtils from '../utils/snap-scene';
import * as SnapUtils from '../utils/snap';
import {
  DEFAULT_AREA_SPLITTER_WIDTH,
  METRICS_EVENTS,
  MIN_WALL_LENGTH_IN_CM,
  MODE_DRAWING_LINE,
  MODE_IDLE,
  MODE_WAITING_DRAWING_LINE,
  POSSIBLE_WALL_WIDTHS,
  REFERENCE_LINE_POSITION,
  SeparatorsType,
} from '../constants';
import {
  AddVertexOptions,
  LineCreateOptions,
  Line as LineType,
  RecreateLineShapeOptions,
  State,
  UpdatedStateObject,
  UpdateLineAuxVerticesOptions,
  Vertex as VertexType,
} from '../types';
import cloneDeep from '../utils/clone-deep';
import { getSelectedLayer } from '../utils/state-utils';
import isScaling from '../utils/is-scaling';
import getFastStateObject from '../utils/get-fast-state-object';
import { ProviderMetrics } from '../providers';
import Project from './project';
import Layer from './layer';
import Hole from './hole';
import Vertex from './vertex';

const DEFAULT_WIDTH = 20;
const getWidthProperty = state => {
  const lastWidth = state.lastWidth || DEFAULT_WIDTH;
  return { width: { value: lastWidth } };
};

const getLengthInCM = (state, layer, line, { x, y }) => {
  const v0 = layer.vertices[line.vertices[0]];
  const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = GeometryUtils.orderVertices([v0, { x, y }]);
  const lengthInPx = GeometryUtils.pointsDistance(x1, y1, x2, y2);
  return GeometryUtils.convertPixelsToCMs(state.scene.scale, lengthInPx);
};

const getLineProperties = (lineType, state, startingLine: any = {}, currentProperties: any = {}) => {
  let lineProperties = currentProperties as any;
  const newReferenceLine =
    lineType === SeparatorsType.AREA_SPLITTER
      ? REFERENCE_LINE_POSITION.OUTSIDE_FACE
      : currentProperties.referenceLine ||
        startingLine.properties?.referenceLine ||
        REFERENCE_LINE_POSITION.OUTSIDE_FACE;

  if (lineType !== SeparatorsType.AREA_SPLITTER) lineProperties = getWidthProperty(state);
  lineProperties = {
    ...lineProperties,
    referenceLine: newReferenceLine,
  };

  return lineProperties;
};

const getNewReferenceLine = (line, possibleReferenceLines) => {
  const currentReferenceLine = line.properties.referenceLine;
  const currentReferenceLineIndex = possibleReferenceLines.indexOf(currentReferenceLine);
  const newReferenceLine = possibleReferenceLines[currentReferenceLineIndex + 1] || possibleReferenceLines[0];
  return newReferenceLine;
};

const getNewWidth = (line, possibleWidthsArray, increment) => {
  const currentWidth = Number(line.properties.width.value);
  const currentWidthIndex = possibleWidthsArray.indexOf(currentWidth);
  const newWidth = possibleWidthsArray[currentWidthIndex + increment] || possibleWidthsArray[0];
  return newWidth;
};

const detectIfPostprocessWillBeValid = (state, layerID, lineID) => {
  const tempState = cloneDeep(state);
  try {
    const { updatedState, postprocessedLineIDs } = PostProcessor.postprocessLines(tempState, layerID, lineID);
    return PostProcessor.isValid(updatedState, postprocessedLineIDs);
  } catch (error) {
    console.error(`Handled error in postprocessing: ${error}`); // Sentry will catch this, but the user won't see it
    return false;
  }
};
class Line {
  static getLineVerticesPoints(line, layerVertices) {
    const vertices = line.vertices;
    const auxVertices = line.auxVertices;
    const allVertices = vertices.concat(auxVertices);

    return allVertices.map(vertexID => {
      const vertex = layerVertices[vertexID];
      return [vertex.x, vertex.y];
    });
  }

  static getPolygon(line) {
    return GeometryUtils.createPolygon(line.coordinates);
  }

  static orderMainVertices(state, layerID, lineID) {
    const layer = state.scene.layers[layerID];
    const line = layer.lines[lineID];

    const lv0 = layer.vertices[line.vertices[0]]; // orderVertices expects objects/records, explicit conversion so this works everytime
    const lv1 = layer.vertices[line.vertices[1]];

    const [v0, v1] = GeometryUtils.orderVertices([lv0, lv1]);
    state.scene.layers[layerID].lines[lineID].vertices = [v0.id, v1.id];

    return { updatedState: state };
  }

  static getAllVerticesInScene(state, layerID) {
    const layer = state.scene.layers[layerID];
    return layer.lines.reduce((acc, otherLine) => {
      const [v0id, v1id] = otherLine.get('vertices');
      return acc.concat(layer.vertices.get(v0id), layer.vertices.get(v1id));
    }, []);
  }

  // @TODO: This method does not modify state, should be outside the class
  static calculateAuxVertices(scene, mainVertices, lineProperties) {
    const [v0, v1] = GeometryUtils.orderVertices(mainVertices);
    const points = { x1: v0.x, y1: v0.y, x2: v1.x, y2: v1.y };
    const referenceLine = lineProperties?.referenceLine;
    const width = lineProperties?.width?.value;
    const scale = scene.scale;
    const scaledWidth = GeometryUtils.convertCMToPixels(scale, width);

    const [offset1, offset2] = GeometryUtils.getOffsetsFromReferenceLine(referenceLine, scaledWidth);

    const [[x2, y2], [x3, y3]] = GeometryUtils.getParallelLinePointsFromOffset(points, offset1);
    const [[x4, y4], [x5, y5]] = GeometryUtils.getParallelLinePointsFromOffset(points, offset2);

    // odd indexes correspond to first main vertex (v0)
    // even indexes correspond to second main vertex (v1)
    return [
      [x2, y2], // neighbours of v0 (first vertex)
      [x3, y3], // neighbours of v1 (second verex)
      [x4, y4], // neighbours of v0 (first vertex)
      [x5, y5], // neighbours of v1 (second vertex)
    ];
  }

  static createAuxVertices(state, mainVertices, lineProperties, layerID, lineID, vertexOptions: AddVertexOptions) {
    // odd indexes correspond to first main vertex (v0)
    // even indexes correspond to second main vertex (v1)
    const auxVerticesPairs = this.calculateAuxVertices(state.scene, mainVertices, lineProperties);

    const createVertexOptions = { ...vertexOptions, fastStateObject: getFastStateObject(state) };

    const auxVertices = auxVerticesPairs.map(pointsPair => {
      const [x, y] = pointsPair;
      const { updatedState, vertex } = Vertex.add(state, layerID, x, y, 'lines', lineID, createVertexOptions);
      state = updatedState;
      return vertex;
    });

    return { updatedState: state, auxVertices };
  }

  static updateLineAuxVertices(
    state,
    properties,
    line,
    layerID,
    lineID,
    options: UpdateLineAuxVerticesOptions = { selectNewVertices: true, force: false }
  ) {
    // Get main vertex to creates aux vertices from its coords
    const layer = state.scene.layers[layerID];
    const [firstVertexId, secondVertexId] = line.vertices;
    const lv0 = layer.vertices[firstVertexId];
    const lv1 = layer.vertices[secondVertexId];
    const vertexOptions = {
      force: line.type === SeparatorsType.AREA_SPLITTER || options.force,
    };

    const auxVertices = line.auxVertices;
    state = auxVertices.reduce(
      (accumulatedState, vertexID) => Vertex.remove(accumulatedState, layerID, vertexID, 'lines', lineID).updatedState,
      state
    );

    const { updatedState, auxVertices: newAuxVertices } = this.createAuxVertices(
      state,
      [lv0, lv1],
      properties,
      layerID,
      lineID,
      vertexOptions
    );
    state = updatedState;

    const newAuxIds = newAuxVertices.map(v => v.id);

    if (options.selectNewVertices) {
      state = newAuxIds.reduce(
        (accumulatedState, vertexID) =>
          Layer.selectElement(accumulatedState, layerID, 'vertices', vertexID).updatedState,
        state
      );
    }
    state.scene.layers[layerID].lines[lineID].auxVertices = newAuxIds;
    return { updatedState: state };
  }

  static create(
    state,
    layerID,
    type,
    x0,
    y0,
    x1,
    y1,
    properties,
    options: LineCreateOptions = { createAuxVertices: true, forceVertexCreation: false }
  ): UpdatedStateObject & { line: LineType } {
    const lineID = IDBroker.acquireID();

    const vertexOptions: AddVertexOptions = {
      force: options.forceVertexCreation || type === SeparatorsType.AREA_SPLITTER,
    };
    // Add main points
    const { updatedState: stateV0, vertex: v0 } = Vertex.add(state, layerID, x0, y0, 'lines', lineID, vertexOptions);
    const { updatedState: stateV1, vertex: v1 } = Vertex.add(stateV0, layerID, x1, y1, 'lines', lineID, vertexOptions);
    state = stateV1;

    let auxVertices = [];
    if (options.createAuxVertices) {
      const { updatedState, auxVertices: newVertices = [] } = this.createAuxVertices(
        state,
        [v0, v1],
        properties,
        layerID,
        lineID,
        vertexOptions
      );
      state = updatedState;
      auxVertices = newVertices;
    }
    const line = state.catalog.factoryElement(
      type,
      {
        id: lineID,
        name: NameGenerator.generateName('lines', state.catalog.elements[type].info.title),
        vertices: [v0.id, v1.id],
        auxVertices: auxVertices.map(v => v.id),
        type,
      },
      properties
    );

    state.scene.layers[layerID].lines[lineID] = line;
    state = this.AddOrUpdateReferenceLineCoords(state, lineID).updatedState;
    const updatedLine = state.scene.layers[layerID].lines[lineID];
    return { updatedState: state, line: updatedLine };
  }

  static duplicate(state, layerID, originalLine) {
    const layer = state.scene.layers[layerID];
    const [firstVertexId, secondVertexId] = originalLine.vertices;
    const v0 = layer.vertices[firstVertexId];
    const v1 = layer.vertices[secondVertexId];

    const { updatedState, line: newLine } = Line.create(
      state,
      layerID,
      originalLine.type,
      v0.x,
      v0.y,
      v1.x,
      v1.y,
      originalLine.properties,
      { createAuxVertices: true, forceVertexCreation: true }
    );

    state = updatedState;

    // Duplicate holes
    originalLine.holes.forEach(originalHoleID => {
      let originalHole = layer.holes[originalHoleID];
      originalHole = {
        ...originalHole,
        line: newLine.id,
      };
      state = Hole.duplicate(state, layerID, originalHole).updatedState; // Will update the relationships also
    });
    const newElement = state.scene.layers[layerID].lines[newLine.id];
    return { updatedState: state, newElement };
  }

  static updateWidthSelectedWalls(state: State, increment) {
    const selectedLayer = state.scene.selectedLayer;
    const allLines = Object.values(state.scene.layers[selectedLayer].lines);
    const [line] = allLines.filter(line => line.selected && line.type !== SeparatorsType.AREA_SPLITTER);
    if (!line) return { updatedState: state }; // Could happen if we press a shortcut while drawing an area splitter
    const newWidth = getNewWidth(line, POSSIBLE_WALL_WIDTHS, increment);
    state = this.updateProperties(state, selectedLayer, line.id, { width: { value: newWidth } }).updatedState;
    // Needed if the user is drawing a wall to apply the width before finishing the drawing
    state.lastWidth = newWidth;
    return { updatedState: state };
  }

  static changeReferenceLine(state) {
    const possibleReferenceLines = Object.values(REFERENCE_LINE_POSITION);
    const selectedLayer = state.scene.selectedLayer;

    if (state.mode !== MODE_DRAWING_LINE) {
      return { updatedState: state };
    }

    const allLines = Object.values(state.scene.layers[selectedLayer].lines) as any;
    const [line] = allLines.filter(line => line.selected && line.type !== SeparatorsType.AREA_SPLITTER);
    if (!line) return { updatedState: state }; // Could happen if we press a shortcut while drawing an area splitter
    const newReferenceLine = getNewReferenceLine(line, possibleReferenceLines);
    state = this.updateProperties(state, selectedLayer, line.id, { referenceLine: newReferenceLine }).updatedState;
    return { updatedState: state };
  }

  static select(state, layerID, lineID, options = { unselectAllBefore: true }) {
    if (options.unselectAllBefore) {
      state = Layer.select(state, layerID).updatedState;
    }

    const line = state.scene.layers[layerID].lines[lineID];

    state = Layer.selectElement(state, layerID, 'lines', lineID).updatedState;

    line.vertices.forEach(vertexID => (state = Layer.selectElement(state, layerID, 'vertices', vertexID).updatedState));

    line.auxVertices.forEach(
      vertexID => (state = Layer.selectElement(state, layerID, 'vertices', vertexID).updatedState)
    );

    return { updatedState: state };
  }

  static remove(state, layerID, lineID, options = { shouldRecreateAreas: true }) {
    const line = state.scene.layers[layerID].lines[lineID];

    if (line) {
      state = this.unselect(state, layerID, lineID).updatedState;
      line.holes.forEach(holeID => (state = Hole.remove(state, layerID, holeID).updatedState));
      state = Layer.removeElement(state, layerID, 'lines', lineID).updatedState;

      line.vertices.forEach(
        vertexID => (state = Vertex.remove(state, layerID, vertexID, 'lines', lineID).updatedState)
      );

      line.auxVertices.forEach(
        vertexID => (state = Vertex.remove(state, layerID, vertexID, 'lines', lineID).updatedState)
      );

      const remainingLines = state.scene.layers[layerID].lines;
      const linesExist = Object.keys(remainingLines).length > 0;
      if (linesExist && options.shouldRecreateAreas) {
        state = Layer.detectAndUpdateAreas(state, layerID).updatedState;
      }
    }

    return { updatedState: state };
  }

  static unselect(state, layerID, lineID) {
    const line = state.scene.layers[layerID].lines[lineID];

    if (line) {
      line.vertices.forEach(vertexID => (state = Layer.unselect(state, layerID, 'vertices', vertexID).updatedState));
      line.auxVertices.forEach(vertexID => (state = Layer.unselect(state, layerID, 'vertices', vertexID).updatedState));
      state = Layer.unselect(state, layerID, 'lines', lineID).updatedState;
    }

    return { updatedState: state };
  }

  static addFromPoints(state, layerID, type, points, properties, holes) {
    points = GeometryUtils.orderVertices(points);

    const pointsPair = [points].filter(([{ x: x1, y: y1 }, { x: x2, y: y2 }]) => !(x1 === x2 && y1 === y2));

    const lines = [];

    pointsPair.forEach(([{ x: x1, y: y1 }, { x: x2, y: y2 }]) => {
      const { updatedState: stateL, line } = this.create(state, layerID, type, x1, y1, x2, y2, properties);
      state = stateL;

      if (holes) {
        holes.forEach(holeWithOffsetPoint => {
          const { x: xp, y: yp } = holeWithOffsetPoint.offsetPosition;

          if (GeometryUtils.isPointOnLineSegment(x1, y1, x2, y2, xp, yp)) {
            const newOffset = GeometryUtils.pointPositionOnLineSegment(x1, y1, x2, y2, xp, yp);

            if (newOffset >= 0 && newOffset <= 1) {
              state = Hole.create(
                state,
                layerID,
                holeWithOffsetPoint.hole.type,
                line.id,
                newOffset,
                holeWithOffsetPoint.hole.properties
              ).updatedState;
            }
          }
        });
      }

      lines.push(line);
    });

    return { updatedState: state, lines: lines };
  }

  static createAvoidingIntersections(state, layerID, type, x0, y0, x1, y1, oldProperties, oldHoles = undefined) {
    const points = [
      { x: x0, y: y0 },
      { x: x1, y: y1 },
    ];

    const { updatedState, lines } = Line.addFromPoints(state, layerID, type, points, oldProperties, oldHoles);
    state = updatedState;
    state = Layer.removeZeroLengthLines(updatedState, layerID).updatedState;

    return { updatedState, lines };
  }

  static calculateCoordinates(referenceLinePoints, line, scale): number[][] {
    const widthInPixels = GeometryUtils.getElementWidthInPixels(line, scale);
    const referenceLine = line.properties.referenceLine;
    return GeometryUtils.getOuterPolygonPointsFromReferenceLine(referenceLinePoints, referenceLine, widthInPixels);
  }

  static AddOrUpdateReferenceLineCoords(state, lineID) {
    const layer = getSelectedLayer(state.scene);
    const line = layer.lines[lineID];
    const vertices = GeometryUtils.orderVertices(line.vertices.map(vertexID => layer.vertices[vertexID]));
    const referenceLinePoints = { x1: vertices[0].x, y1: vertices[0].y, x2: vertices[1].x, y2: vertices[1].y };
    const points: number[][] = this.calculateCoordinates(referenceLinePoints, line, state.scene.scale);
    state.scene.layers[layer.id].lines[line.id].coordinates = [points];
    return { updatedState: state };
  }

  static replaceVertex(state, layerID, lineID, vertexIndex, x, y, vertexOptions = { force: false }) {
    const vertexID = state.scene.layers[layerID].lines[lineID].vertices[vertexIndex];

    state = Vertex.remove(state, layerID, vertexID, 'lines', lineID).updatedState;
    const { updatedState: stateV, vertex } = Vertex.add(state, layerID, x, y, 'lines', lineID, vertexOptions);
    state = stateV;

    const vertices = [...state.scene.layers[layerID].lines[lineID].vertices];
    vertices[vertexIndex] = vertex.id;

    state.scene.layers[layerID].lines[lineID].vertices = vertices;
    const newLine = state.scene.layers[layerID].lines[lineID];

    state.scene.layers[layerID].lines[lineID] = newLine;

    return { updatedState: state, line: state.scene.layers[layerID].lines[lineID], vertex };
  }

  static selectToolDrawingLine(state, sceneComponentType) {
    if (state.mode === MODE_DRAWING_LINE) {
      const sceneHistory = state.sceneHistory;
      const isDrawing = state.drawingSupport.drawingStarted;
      const sceneHistoryListIsNotEmpty = sceneHistory.list.length !== 0;
      if (sceneHistoryListIsNotEmpty && isDrawing) {
        state.scene = sceneHistory.last;
        state.snapElements = [];
        state.activeSnapElement = null;
        state.sceneHistory = history.historyPop(sceneHistory);
      }
    }
    state.mode = MODE_WAITING_DRAWING_LINE;
    state.drawingSupport = {
      type: sceneComponentType,
    };

    return { updatedState: state };
  }

  /*
    Current flow is:
     - Create a deep copy of the state, apply postprocessing and check that is valid.
     - If is valid, postprocess again on the original state, otherwise, do nothing.
     
    The original flow consisted on:
      - Create a copy of the state
      - Apply postprocessing of the original state
         - Wrong? -> Use the copy
         - Valid? -> Use the postprocessed version

     But then immer.js will complain that we are modifying the draft and cloning it in the wrong case, so we cannot do this and have to do the other flow.
  */

  static postprocess(state, layerID, lineID) {
    const tempState = getFastStateObject(state);
    const postprocessWillBeValid = detectIfPostprocessWillBeValid(tempState, layerID, lineID);
    if (postprocessWillBeValid) {
      state = PostProcessor.postprocessLines(state, layerID, lineID).updatedState;
    }
    return { updatedState: state };
  }

  static beginDrawingLine(state: State, layerID, x, y) {
    if (!isScaling(state)) {
      ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_LINE);
    }
    let snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(state.scene, [], state.snapMask, null, x, y);
    let snap = null;

    const layer = state.scene.layers[layerID];
    const snapMaskIsNotEmpty = Object.keys(state.snapMask).length !== 0;
    const isSnapEnabled = state.snapMask && snapMaskIsNotEmpty;

    if (isSnapEnabled) {
      snap = SnapUtils.nearestSnap(snapElements, x, y, state.snapMask);
      if (snap) ({ x, y } = snap.point);
    }

    const startingLine = GeometryUtils.getStartingLineFromPoint(layer, { x: x, y: y });

    if (isSnapEnabled) {
      snapElements = SnapUtils.addPerpendicularSnapLines(state.scene, snapElements, { x, y }, layer);
    }
    const drawingSupport: State['drawingSupport'] = {
      ...state.drawingSupport,
      layerID,
      drawingStarted: true,
    };

    state = Layer.unselectAll(state, layerID).updatedState;

    const lineType = drawingSupport.type;

    if (isScaling(state) && !startingLine) {
      state = Project.removeScalingLines(state).updatedState;
    }

    const initialProperties = getLineProperties(lineType, state, startingLine);
    /**
     * We need to forceVertexCreation because:
     * In updateDrawingLine we're replacing the 2nd vertex (index 1)
     * In this case, we're passing x, y for both vertices and if they're not forcefully created there will be only 1 vertex added to the state with the same ID
     * Which later in replaceVertex will lead into error, more precisely it will change the 1st vertex as well
     */
    const { updatedState: stateL, line } = Line.create(state, layerID, lineType, x, y, x, y, initialProperties, {
      createAuxVertices: false,
      forceVertexCreation: true,
    });

    state = Line.select(stateL, layerID, line.id).updatedState;

    state.mode = MODE_DRAWING_LINE;
    state.snapElements = snapElements;
    state.activeSnapElement = snap ? snap.snap : null;
    state.drawingSupport = drawingSupport;

    return { updatedState: state };
  }

  static updateDrawingLine(state, x, y) {
    const layerID = state.drawingSupport.layerID;
    const layer = state.scene.layers[layerID];
    const lineID = state.scene.layers[layerID].selected.lines[0];
    const line = state.scene.layers[layerID].lines[lineID];

    const snapElements = SnapSceneUtils.sceneSnapNearestElementsLine(
      state.scene,
      state.snapElements,
      state.snapMask,
      lineID,
      x,
      y
    );
    let snap = null;

    const snapMaskIsNotEmpty = Object.keys(state.snapMask).length !== 0;
    if (state.snapMask && snapMaskIsNotEmpty) {
      snap = SnapUtils.nearestSnap(snapElements, x, y, state.snapMask);

      if (snap) {
        const vertexId = line.vertices[0];
        const v0 = layer.vertices[vertexId];
        const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = GeometryUtils.orderVertices([v0, { x, y }]);
        const lengthInPx = GeometryUtils.pointsDistance(x1, y1, x2, y2);

        const lineLengthGreaterThanSnapDistance = lengthInPx > snap.point.distance; // Otherwise the line will snap to the point and won't be created
        if (lineLengthGreaterThanSnapDistance) ({ x, y } = snap.point);
      }
    }

    const { updatedState: stateLV } = Line.replaceVertex(state, layerID, lineID, 1, x, y, {
      force: true,
    });
    state = stateLV;

    state = this.select(state, layerID, lineID).updatedState;

    const updatedLine = state.scene.layers[layerID].lines[lineID];
    state = this.updateLineAuxVertices(state, updatedLine.properties, updatedLine, layerID, lineID).updatedState;
    state = this.AddOrUpdateReferenceLineCoords(state, lineID).updatedState;
    state.snapElements = snapElements;
    state.activeSnapElement = snap ? snap.snap : null;

    if (isScaling(state)) {
      const allLines = Object.values(state.scene.layers[layerID].lines) as any;
      const nrOfScaleLines = allLines.filter(line => line.type === SeparatorsType.SCALE_TOOL).length;

      if (nrOfScaleLines === 1) {
        const lengthInCM = getLengthInCM(state, layer, line, { x, y });
        state = Project.setScaleToolProperties(state, { distance: (lengthInCM / 100).toFixed(2) }).updatedState;
      }
    }

    return { updatedState: state };
  }

  static endDrawingLine(state, x, y) {
    const layerID = state.drawingSupport.layerID;
    const layer = state.scene.layers[layerID];

    const lineID = layer.selected.lines[0];
    const line = layer.lines[lineID];

    const [firstVertexId, secondVertexId] = line.vertices;
    const v0 = layer.vertices[firstVertexId];
    const v1 = layer.vertices[secondVertexId];

    state = Line.remove(state, layerID, lineID, { shouldRecreateAreas: false }).updatedState;

    const lengthInPx = GeometryUtils.pointsDistance(v0.x, v0.y, v1.x, v1.y);
    const lengthInCM = GeometryUtils.convertPixelsToCMs(state.scene.scale, lengthInPx);
    if (lengthInCM < MIN_WALL_LENGTH_IN_CM) {
      return { updatedState: state };
    }

    const snapMaskIsNotEmpty = Object.keys(state.snapMask).length !== 0;
    if (state.snapMask && snapMaskIsNotEmpty) {
      const snap = SnapUtils.nearestSnap(state.snapElements, x, y, state.snapMask);
      if (snap) {
        const lineLengthGreaterThanSnapDistance = lengthInPx > snap.point.distance; // Otherwise the line will snap to the point and won't be created
        if (lineLengthGreaterThanSnapDistance) ({ x, y } = snap.point);
      }
    }

    const startingLine = GeometryUtils.getStartingLineFromPoint(layer, { x: v0.x, y: v0.y });

    const additionalProperties = getLineProperties(line.type, state, startingLine, line.properties);

    const { updatedState: updatedState, lines: lines } = Line.createAvoidingIntersections(
      state,
      layerID,
      line.type,
      v0.x,
      v0.y,
      x,
      y,
      additionalProperties
    );
    // We should have created only 1 line here
    const newLineID = lines[0].id;
    state = this.AddOrUpdateReferenceLineCoords(updatedState, newLineID).updatedState;

    state = this.postprocess(state, layerID, newLineID).updatedState;

    state = Layer.detectAndUpdateAreas(state, layerID, { detectScaleAreasOnly: isScaling(state) }).updatedState;

    if (isScaling(state)) {
      // Sync current "scale area" size and scale tool
      const layer = state.scene.layers[layerID];
      const allAreas = Object.values(layer.areas) as any;
      const scaleArea = allAreas.find(a => a.isScaleArea);
      if (scaleArea) {
        const areaSize = GeometryUtils.getAreaSizeFromScale(scaleArea, state.scene.scale);
        state = Project.setScaleToolProperties(state, { areaSize }).updatedState;
      }
    }

    state.mode = MODE_WAITING_DRAWING_LINE;
    state.snapElements = [];
    state.activeSnapElement = null;
    state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);

    if (!isScaling(state)) {
      ProviderMetrics.endTrackingEvent(METRICS_EVENTS.DRAWING_LINE);
    }

    return { updatedState: state };
  }

  //@TODO: All options should be inside options object, not as additional parameters
  static recreateLineShape(
    state,
    layerID,
    lineID,
    reloadAreas = true,
    options: RecreateLineShapeOptions = { adjustHoles: true, auxVerticesOptions: undefined },
    shouldUpdateAuxVertices = true
  ) {
    /**
     * Reapplies post-processing changes to all of the intersecting with the target line
     * given by the lineID whenever there has been any mutation to the target line properties.
     */
    const line = state.scene.layers[layerID].lines[lineID];
    if (shouldUpdateAuxVertices) {
      state = this.updateLineAuxVertices(state, line.properties, line, layerID, lineID, options.auxVerticesOptions)
        .updatedState;
    }
    state = this.AddOrUpdateReferenceLineCoords(state, lineID).updatedState;

    if (options.adjustHoles) {
      line.holes.forEach(holeID => {
        state = Hole.adjustHolePolygonAfterLineChange(state, layerID, holeID).updatedState;
      });
    }

    if (state.mode == MODE_IDLE) {
      const layer = getSelectedLayer(state.scene);
      const intersectingLines = GeometryUtils.getPostProcessableIntersectingLines(layer, line.id);
      intersectingLines.forEach(l => {
        state = this.AddOrUpdateReferenceLineCoords(state, l.id).updatedState;
      });
      state = this.postprocess(state, layerID, line.id).updatedState;
    }
    if (reloadAreas) {
      state = Layer.detectAndUpdateAreas(state, layerID).updatedState;
    }
    return { updatedState: state };
  }

  static setProperties(state, layerID, lineID, properties) {
    state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);

    state.scene.layers[layerID].lines[lineID].properties = {
      ...state.scene.layers[layerID].lines[lineID].properties,
      ...properties,
    };

    const line = state.scene.layers[layerID].lines[lineID];
    if (properties.width && line.type !== SeparatorsType.AREA_SPLITTER) {
      state.lastWidth = properties.width.value;
    }
    const shouldRecreateAreas = state.mode === MODE_IDLE;
    state = this.recreateLineShape(state, layerID, lineID, shouldRecreateAreas).updatedState;
    return { updatedState: state };
  }

  static updateProperties(state: State, layerID, lineID, properties) {
    state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
    const propertiesEntries = Object.entries(properties) as any;

    propertiesEntries.forEach(([k, v]) => {
      const lineHasProperty = state.scene.layers[layerID].lines[lineID].properties.hasOwnProperty(k);
      if (lineHasProperty) {
        state.scene.layers[layerID].lines[lineID].properties = {
          ...state.scene.layers[layerID].lines[lineID].properties,
          [k]: v,
        };
      }
    });
    const shouldRecreateAreas = state.mode === MODE_IDLE;
    return this.recreateLineShape(state, layerID, lineID, shouldRecreateAreas);
  }

  static setAttributes(state, layerID, lineID, lineAttributes) {
    const lAttr = lineAttributes;
    const { vertexOne, vertexTwo, lineLength } = lAttr;

    delete lAttr['vertexOne'];
    delete lAttr['vertexTwo'];
    delete lAttr['lineLength'];

    state.scene.layers.lines[lineID] = lAttr;
    state.scene.layers.vertices[vertexOne.id] = { x: vertexOne.x, y: vertexOne.y };
    state.scene.layers.vertices[vertexTwo.id] = { x: vertexTwo.x, y: vertexTwo.y };
    state.scene.layers.lines[lineID].misc = { _unitLength: lineLength._unit };

    state = Layer.mergeEqualsVertices(state, layerID, vertexOne.id).updatedState;

    if (vertexOne.x != vertexTwo.x && vertexOne.y != vertexTwo.y) {
      state = Layer.mergeEqualsVertices(state, layerID, vertexTwo.id).updatedState;
    }

    state = Layer.detectAndUpdateAreas(state, layerID).updatedState;

    return { updatedState: state };
  }

  static replaceVertices(
    state: State,
    layerID: string,
    lineID: string,
    newVertex: VertexType,
    vertexToReplace: VertexType
  ): UpdatedStateObject {
    const line = state.scene.layers[layerID].lines[lineID];
    let newAuxVertices = line.auxVertices;
    if (line.auxVertices.includes(vertexToReplace.id)) {
      newAuxVertices = line.auxVertices.map(id => (id === vertexToReplace.id ? newVertex.id : id));
    }
    let newVertices = line.vertices;
    if (line.vertices.includes(vertexToReplace.id)) {
      newVertices = line.vertices.map(id => (id === vertexToReplace.id ? newVertex.id : id));
    }
    state.scene.layers[layerID].lines[lineID].vertices = newVertices;
    state.scene.layers[layerID].lines[lineID].auxVertices = newAuxVertices;

    state = Vertex.addElement(state, layerID, newVertex.id, 'lines', lineID).updatedState;
    state = Vertex.remove(state, layerID, vertexToReplace.id, 'lines', lineID).updatedState;
    return { updatedState: state };
  }

  static changeLineType(state, lineId, lineType) {
    const isAreaSplitter = SeparatorsType.AREA_SPLITTER === lineType;
    const shouldRemoveHoles = SeparatorsType.WALL !== lineType;
    const selectedLayer = state.scene.selectedLayer;
    const selectedLine = state.scene.layers[selectedLayer].lines[lineId];
    const layer = state.scene.layers[selectedLayer];

    // Railings, columns and area splitters can not have any holes
    if (shouldRemoveHoles) {
      selectedLine.holes.forEach(holeID => (state = Hole.remove(state, selectedLayer, holeID).updatedState));
    }

    if (isAreaSplitter) {
      const defaultAreaSplitterProperties = {
        height: { value: 300 },
        referenceLine: 'OUTSIDE_FACE',
        width: { value: DEFAULT_AREA_SPLITTER_WIDTH },
      };
      state = Line.updateProperties(state, selectedLayer, lineId, defaultAreaSplitterProperties).updatedState;
    }

    const v0 = layer.vertices[selectedLine.vertices[0]];
    const startingLine = GeometryUtils.getStartingLineFromPoint(layer, { x: v0.x, y: v0.y });
    const nextProperties = getLineProperties(lineType, state, startingLine, selectedLine.properties) as any;
    const prevAreaSplitter = selectedLine.type === SeparatorsType.AREA_SPLITTER;
    const isNotAreaSplitter = SeparatorsType.AREA_SPLITTER !== lineType;
    if (isNotAreaSplitter && prevAreaSplitter) {
      const defaultProperties = {
        height: { value: 300 },
        referenceLine: nextProperties.referenceLine,
        width: nextProperties.width,
      };
      state = Line.updateProperties(state, selectedLayer, lineId, defaultProperties).updatedState;
    }

    const name = lineType.split('_').map(capitalize).join(' ');
    state.scene.layers[selectedLayer].lines[lineId].name = name;
    state.scene.layers[selectedLayer].lines[lineId].type = lineType;

    return { updatedState: state };
  }

  static changeLinesType(state, lineIds, lineType) {
    lineIds.forEach(lineId => {
      state = this.changeLineType(state, lineId, lineType).updatedState;
    });
    return { updatedState: state };
  }
}

export { Line as default };
