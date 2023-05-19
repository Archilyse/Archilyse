import * as GeometryUtils from '../utils/geometry';
import * as history from '../utils/history';
import IDBroker from '../utils/id-broker';
import NameGenerator from '../utils/name-generator';
import * as SnapSceneUtils from '../utils/snap-scene';
import cloneDeep from '../utils/clone-deep';
import { nearestSnap } from '../utils/snap';
import { doorHasWings, getSelected, getSelectedLayer } from '../utils/state-utils';
import {
  METRICS_EVENTS,
  MIN_HOLE_LENGTH,
  MODE_DRAGGING_HOLE,
  MODE_DRAWING_HOLE,
  MODE_IDLE,
  PrototypesEnum,
  SeparatorsType,
} from '../constants';
import { Hole as HoleType, Line as LineType, OpeningType, State, UpdatedStateObject } from '../types';
import { ProviderMetrics } from '../providers';
import Layer from './layer';

const getNextRotationProperties = hole => {
  const { flip_horizontal, flip_vertical } = hole.properties;
  if (!flip_horizontal && !flip_vertical) {
    // 0 0 -> 0 1
    return { flip_horizontal: false, flip_vertical: true };
  }
  if (!flip_horizontal && flip_vertical) {
    // 0 1 -> 1 1
    return { flip_horizontal: true, flip_vertical: true };
  }
  if (flip_horizontal && flip_vertical) {
    // 1 1 -> 1 0
    return { flip_horizontal: true, flip_vertical: false };
  }
  if (flip_horizontal && !flip_vertical) {
    // 1 0 -> 0 0
    return { flip_horizontal: false, flip_vertical: false };
  }
};

export const openingOverlappingOtherOpenings = (
  state,
  snapPoint,
  lineId,
  holeID,
  otherHoles,
  properties: any = {}
): boolean => {
  const holeCoordinates = Hole.getPolygonPoints(state, lineId, snapPoint, {
    openingLengthInCm: properties.length?.value,
    holeID: holeID,
  });
  const newOpeningPolygon = GeometryUtils.createPolygon([holeCoordinates]);
  return otherHoles.some(otherHole => {
    const otherOpeningPolygon = GeometryUtils.createPolygon(otherHole.coordinates);
    return GeometryUtils.booleanIntersects(newOpeningPolygon, otherOpeningPolygon);
  });
};

class Hole {
  static create(
    state,
    layerID,
    type,
    lineID,
    coordinates,
    sweepingPoints = undefined,
    properties = undefined
  ): UpdatedStateObject & { hole: HoleType } {
    const holeID = IDBroker.acquireID();

    const hole = state.catalog.factoryElement(
      type,
      {
        id: holeID,
        name: NameGenerator.generateName('holes', state.catalog.elements[type].info.title),
        type,
        line: lineID,
        coordinates: coordinates,
        door_sweeping_points: sweepingPoints,
      },
      properties
    );

    state.scene.layers[layerID].holes[holeID] = hole;

    // When copypasting between plans we can create holes without lines
    if (lineID) {
      const holes = state.scene.layers[layerID].lines[lineID].holes;
      const newHoles = holes.concat(holeID);
      state.scene.layers[layerID].lines[lineID].holes = newHoles;
    }
    return { updatedState: state, hole };
  }

  static duplicate(state, layerID, originalHole): UpdatedStateObject & { newElement: HoleType } {
    const { updatedState, hole: newElement } = Hole.create(
      state,
      layerID,
      originalHole.type,
      originalHole.line,
      originalHole.coordinates,
      originalHole.door_sweeping_points,
      originalHole.properties
    );

    return { updatedState, newElement };
  }

  static holeOutsideParentLine(state, snapPoint, layerID, holeID, properties): boolean {
    const hole = state.scene.layers[layerID].holes[holeID];
    const parentLine = state.scene.layers[layerID].lines[hole.line];
    const holeCoordinates = Hole.getPolygonPoints(state, parentLine.id, snapPoint, {
      openingLengthInCm: properties.length.value,
      holeID: holeID,
    });
    const holePolygon = GeometryUtils.createPolygon([holeCoordinates]);
    const holePolygonCenterline = GeometryUtils.getPolygonCenterLine(holePolygon);
    const linePolygon = GeometryUtils.createPolygon(parentLine.coordinates);
    return !GeometryUtils.booleanWithin(holePolygonCenterline, linePolygon);
  }

  static areNewPropertiesValid(state, layerID, holeID, properties): boolean {
    const layer = state.scene.layers[layerID];
    const hole = layer.holes[holeID];
    const line = layer.lines[hole.line];

    const otherHoles = line.holes.filter(subHoleID => subHoleID != hole.id).map(subHoleID => layer.holes[subHoleID]);

    const [cx, cy] = GeometryUtils.getFeatureCentroid(hole.coordinates[0]);
    const holeWillOverlap = openingOverlappingOtherOpenings(
      state,
      { x: cx, y: cy },
      line.id,
      hole.id,
      otherHoles,
      properties
    );
    const holeOutsideLine = this.holeOutsideParentLine(state, { x: cx, y: cy }, layerID, holeID, properties);
    return !holeWillOverlap && !holeOutsideLine;
  }

  static updateDoorSweepingPoints(state: State, holeID): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    const hole = state.scene.layers[selectedLayer].holes[holeID];
    const [cx, cy] = GeometryUtils.getFeatureCentroid(hole.coordinates[0]);
    const [vertex0, vertex1] = this.getOpeningShortSideMidPoints(state, { x: cx, y: cy }, holeID);
    const sweepingPoints = this.getDoorSweepingPoints(
      vertex0,
      vertex1,
      hole.properties.flip_horizontal,
      hole.properties.flip_vertical
    );

    state.scene.layers[selectedLayer].holes[hole.id].door_sweeping_points = sweepingPoints;

    return { updatedState: state };
  }

  static updateLengthMeasuresSelectedHoles(state, lengthInc): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    const allHoles: HoleType[] = Object.values(state.scene.layers[selectedLayer].holes);
    const hole = allHoles.filter(hole => hole.selected)[0];

    const currentLength = hole.properties.length.value;
    const newLength = currentLength + lengthInc < MIN_HOLE_LENGTH ? currentLength : currentLength + lengthInc;
    const updatedLengthMeasures = {
      length: { value: newLength },
    };

    if (!this.areNewPropertiesValid(state, selectedLayer, hole.id, updatedLengthMeasures))
      return { updatedState: state };
    state = this.updateProperties(state, selectedLayer, hole.id, updatedLengthMeasures).updatedState;

    const [cx, cy] = GeometryUtils.getFeatureCentroid(hole.coordinates[0]);
    const coords = this.getPolygonPoints(
      state,
      hole.line,
      { x: cx, y: cy },
      { holeID: hole.id, openingLengthInCm: undefined }
    );
    state.scene.layers[selectedLayer].holes[hole.id].coordinates = [coords];

    if (doorHasWings(hole.type)) {
      state = this.updateDoorSweepingPoints(state, hole.id).updatedState;
    }
    return { updatedState: state };
  }

  static select(state, layerID, holeID, options = { unselectAllBefore: true }): UpdatedStateObject {
    if (options.unselectAllBefore) {
      state = Layer.select(state, layerID).updatedState;
    }
    state = Layer.selectElement(state, layerID, 'holes', holeID).updatedState;

    return { updatedState: state };
  }

  static rotateSelectedDoors(state): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;
    const allHoles: HoleType[] = Object.values(state.scene.layers[selectedLayer].holes);
    allHoles
      .filter(hole => hole.selected && hole.type !== 'window')
      .forEach(hole => {
        const holeId = hole.id;

        const rotationProperties = getNextRotationProperties(hole);
        state = this.updateProperties(state, selectedLayer, holeId, rotationProperties).updatedState;
        if (doorHasWings(hole.type)) {
          state = this.updateDoorSweepingPoints(state, holeId).updatedState;
        }
      });

    return { updatedState: state };
  }

  static remove(state, layerID, holeID): UpdatedStateObject {
    const hole = state.scene.layers[layerID].holes[holeID];
    if (hole) {
      state = this.unselect(state, layerID, holeID).updatedState;
      state = Layer.removeElement(state, layerID, 'holes', holeID).updatedState;

      // When copypasting between plans we can create holes without lines
      if (hole?.line) {
        const filteredHoles = state.scene.layers[layerID].lines[hole.line].holes.filter(id => holeID !== id);
        state.scene.layers[layerID].lines[hole.line].holes = filteredHoles;
      }
    }

    return { updatedState: state };
  }

  static unselect(state, layerID, holeID): UpdatedStateObject {
    state = Layer.unselect(state, layerID, 'holes', holeID).updatedState;

    return { updatedState: state };
  }

  static selectToolDrawingHole(state, sceneComponentType): UpdatedStateObject {
    const selectedLayer = state.scene.selectedLayer;

    state = Layer.unselectAll(state, selectedLayer).updatedState;

    if (state.mode === MODE_DRAWING_HOLE) {
      const sceneHistory = state.sceneHistory;
      const isDrawing = state.drawingSupport.drawingStarted;
      const sceneHistoryIsNotEmpty = sceneHistory.list.length !== 0;

      if (sceneHistoryIsNotEmpty && isDrawing) {
        state.scene = sceneHistory.last;
        state.sceneHistory = history.historyPop(sceneHistory);
      }
    }

    state.mode = MODE_DRAWING_HOLE;
    state.drawingSupport = {
      type: sceneComponentType,
    };

    return { updatedState: state };
  }

  static openingOverValidSeparator(lineType: typeof SeparatorsType[keyof typeof SeparatorsType]): boolean {
    if (lineType == SeparatorsType.WALL) {
      return true;
    }
    return false;
  }

  static getCurrentHole(state): HoleType {
    const scene = state.scene;
    const layerID = getSelectedLayer(scene).id;
    const selectedHoleID = scene.layers[layerID].selected.holes[0];

    if (selectedHoleID) {
      return scene.layers[layerID].holes[selectedHoleID];
    }
    return state.catalog.factoryElement(state.drawingSupport.type);
  }

  static addHoleSnaps(state, x, y): UpdatedStateObject {
    const currentHole = this.getCurrentHole(state);

    const snapElements = SnapSceneUtils.sceneSnapHoleNearestLine(state.scene, [], currentHole, x, y);
    state.snapElements = snapElements;

    return { updatedState: state };
  }

  static updateLineAndCoordinates(
    state: State,
    hole: HoleType,
    newLine: LineType,
    layerID: string,
    selectedHoleID: string,
    snap: { point: { x: number; y: number } }
  ): UpdatedStateObject {
    //1. If the current hole belongs to a different line (line is taken from snaps), replace it
    const currentLineID = hole.line;
    const isInADifferentLine = currentLineID && currentLineID !== newLine.id;

    if (isInADifferentLine) {
      state = this.replaceLines(state, hole.id, currentLineID, newLine.id).updatedState;
    }
    // 2. Add the line to the hole (hole.line = '...') and update its coordiantes
    const coordinates = [this.getPolygonPoints(state, newLine.id, snap.point)];
    state.scene.layers[layerID].holes[selectedHoleID].line = newLine.id;
    state.scene.layers[layerID].holes[selectedHoleID].coordinates = coordinates;

    //3. Add the hole to the line (line.holes=[...])
    if (!newLine.holes.includes(selectedHoleID)) {
      const lineHoles = state.scene.layers[layerID].lines[newLine.id].holes;
      const newHoleIds = lineHoles.concat(selectedHoleID);
      state.scene.layers[layerID].lines[newLine.id].holes = newHoleIds;
    }

    // 4. Update door sweeping points
    const holeType: OpeningType = state.drawingSupport.type;
    if (doorHasWings(holeType)) {
      state = this.updateDoorSweepingPoints(state, hole.id).updatedState;
    }
    return { updatedState: state };
  }

  static updateDrawingHole(state, layerID, x, y): UpdatedStateObject {
    ProviderMetrics.startTrackingEvent(METRICS_EVENTS.DRAWING_OPENING);

    state = this.addHoleSnaps(state, x, y).updatedState;
    //calculate snap and overwrite coords if needed
    //force snap to segment
    const newSnapMask = { ...state.snapMask, SNAP_SEGMENT: true };
    const snap = nearestSnap(state.snapElements, x, y, newSnapMask);
    if (!snap) return { updatedState: state };
    ({ x, y } = snap.point);

    const lineID = snap.snap.metadata['lineID'];
    const layer = state.scene.layers[layerID];
    const line = layer.lines[lineID];

    if (!this.openingOverValidSeparator(line.type)) {
      return { updatedState: state };
    }

    const currentHole = this.getCurrentHole(state);
    const selectedHoleID = state.scene.layers[layerID].selected.holes[0];
    const otherHoles = line.holes
      .filter(subHoleID => subHoleID != selectedHoleID)
      .map(subHoleID => layer.holes[subHoleID]);

    if (openingOverlappingOtherOpenings(state, snap.point, lineID, selectedHoleID, otherHoles)) {
      return { updatedState: state };
    }
    //if hole does exist, update
    if (selectedHoleID) {
      state = this.updateLineAndCoordinates(state, currentHole, line, layerID, selectedHoleID, snap).updatedState;
    } else {
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      state.drawingSupport = { ...state.drawingSupport, drawingStarted: true };

      //if hole does not exist, create
      const holeType = state.drawingSupport.type;
      const coordinates = this.getPolygonPoints(state, line.id, snap.point);
      const { updatedState, hole } = this.create(state, layerID, holeType, lineID, [coordinates]);

      state = updatedState;
      if (doorHasWings(holeType)) {
        state = this.updateDoorSweepingPoints(state, hole.id).updatedState;
      }

      state = Hole.select(state, layerID, hole.id).updatedState;
      const properties = state.drawingSupport.properties;
      if (properties) {
        state = this.setProperties(state, layerID, hole.id, properties, false).updatedState;
      }
    }
    return { updatedState: state };
  }

  static updateDraggingHole(state, x, y): UpdatedStateObject {
    //calculate snap and overwrite coords if needed
    //force snap to segment
    const snapMask = {
      ...state.snapMask,
      SNAP_SEGMENT: true,
    };
    const snap = nearestSnap(state.snapElements, x, y, snapMask);
    if (!snap) return { updatedState: state };
    ({ x, y } = snap.point);

    const { draggingSupport } = state;

    const layerID = draggingSupport.layerID;
    const holeID = draggingSupport.holeID;

    const layer = state.scene.layers[layerID];
    const hole = layer.holes[holeID];
    const line = layer.lines[hole.line];

    if (!this.openingOverValidSeparator(line.type)) {
      return { updatedState: state };
    }

    // Now I need min and max possible coordinates for the hole on the line. They depend on the length of the hole
    const otherHoles = line.holes.filter(subHoleID => subHoleID != holeID).map(subHoleID => layer.holes[subHoleID]);

    if (openingOverlappingOtherOpenings(state, snap.point, line.id, holeID, otherHoles)) {
      return { updatedState: state };
    }

    const coordinates = [this.getPolygonPoints(state, line.id, snap.point)];
    state.scene.layers[layerID].holes[holeID].coordinates = coordinates;

    if (doorHasWings(hole.type)) {
      state = this.updateDoorSweepingPoints(state, hole.id).updatedState;
    }

    const newLineID = snap.snap.metadata['lineID'];
    const currentLineID = line.id;

    const isInADifferentLine = currentLineID && currentLineID !== newLineID;
    if (isInADifferentLine) {
      state = this.replaceLines(state, hole.id, currentLineID, newLineID).updatedState;
    }
    return { updatedState: state };
  }

  static endDrawingHole(state: State, layerID, x, y): UpdatedStateObject {
    state = this.updateDrawingHole(state, layerID, x, y).updatedState;
    state = Layer.unselectAll(state, layerID).updatedState;

    ProviderMetrics.endTrackingEvent(METRICS_EVENTS.DRAWING_OPENING);
    return { updatedState: state };
  }

  static beginDraggingHole(state, layerID, holeID, x, y): UpdatedStateObject {
    state.mode = MODE_DRAGGING_HOLE;
    state.draggingSupport = {
      layerID,
      holeID,
      startPointX: x,
      startPointY: y,
    };

    state = Hole.select(state, layerID, holeID).updatedState;
    state = this.addHoleSnaps(state, x, y).updatedState;

    return { updatedState: state };
  }

  static endDraggingHole(state, x, y): UpdatedStateObject {
    state = this.updateDraggingHole(state, x, y).updatedState;

    state.mode = MODE_IDLE;
    state.snapElements = [];
    return { updatedState: state };
  }

  static copySelectedHole(state): UpdatedStateObject {
    const hole = getSelected(state.scene, PrototypesEnum.HOLES);
    if (!hole) return { updatedState: state };

    state = this.selectToolDrawingHole(state, hole.type).updatedState;
    state.drawingSupport = { ...state.drawingSupport, properties: hole.properties };

    return { updatedState: state };
  }

  // IMPORTANT: This returns the polygon without the sweeping points
  static getPolygon(hole: HoleType) {
    return GeometryUtils.createPolygon(hole.coordinates);
  }

  static getPolygonPoints(state, lineId, snapPoint, options = { openingLengthInCm: undefined, holeID: undefined }) {
    const scene = state.scene;
    const layer = getSelectedLayer(scene);
    const referenceLine = layer.lines[lineId];
    const currentHole = options.holeID ? layer.holes[options.holeID] : this.getCurrentHole(state);
    const [v0, v1] = GeometryUtils.orderVertices(referenceLine.vertices.map(vertexID => layer.vertices[vertexID]));

    const lineWidthInPixels = GeometryUtils.getElementWidthInPixels(referenceLine, scene.scale);
    const openingLengthInPixels = options.openingLengthInCm
      ? GeometryUtils.convertCMToPixels(scene.scale, options.openingLengthInCm)
      : GeometryUtils.getElementLengthInPixels(currentHole, scene.scale);

    const tetha = GeometryUtils.angleBetweenTwoPointsAndOrigin(v0.x, v0.y, v1.x, v1.y);

    const allOpeningPoints = GeometryUtils.getOpeningPolygonPointsFromSnap(
      snapPoint,
      openingLengthInPixels,
      lineWidthInPixels,
      tetha
    );
    return allOpeningPoints;
  }

  static getOpeningShortSideMidPoints(state, { x, y }, holeID) {
    const scene = state.scene;
    const layer = getSelectedLayer(scene);
    const currentHole = layer.holes[holeID];
    const parentLine = layer.lines[currentHole.line];
    const [v0, v1] = parentLine.vertices.map(vertexID => layer.vertices[vertexID]);

    const openingLengthInPx = GeometryUtils.getElementLengthInPixels(currentHole, scene.scale);
    const tetha = GeometryUtils.angleBetweenTwoPointsAndOrigin(v0.x, v0.y, v1.x, v1.y);

    const width = openingLengthInPx / 2;

    const points = [
      GeometryUtils.rotatePointAroundPoint(x - width, y, x, y, tetha),
      GeometryUtils.rotatePointAroundPoint(x + width, y, x, y, tetha),
    ];
    return GeometryUtils.orderVertices(points);
  }

  static getDoorSweepingPoints(vertex0, vertex1, flipHorizontal, flipVertical): HoleType['door_sweeping_points'] {
    const [{ x: anglePointX, y: anglePointY }, { x: closedPointX, y: closedPointY }] = flipVertical
      ? [vertex1, vertex0]
      : [vertex0, vertex1];
    const rotationAngle = flipHorizontal ^ flipVertical ? -90 : 90;
    const openedPoint = GeometryUtils.rotatePointAroundPoint(
      closedPointX,
      closedPointY,
      anglePointX,
      anglePointY,
      rotationAngle
    );
    const sweepingPoints: HoleType['door_sweeping_points'] = {
      angle_point: [anglePointX, anglePointY],
      closed_point: [closedPointX, closedPointY],
      opened_point: [openedPoint.x, openedPoint.y],
    };
    return sweepingPoints;
  }

  static recalculateHolePolygon(state, layerID, holeID, referencePoint = undefined) {
    const hole = state.scene.layers[layerID].holes[holeID];
    const [x, y] = referencePoint ? referencePoint : GeometryUtils.getFeatureCentroid(hole.coordinates[0]);
    const coordinates = this.getPolygonPoints(
      state,
      hole.line,
      { x, y },
      { holeID: holeID, openingLengthInCm: undefined }
    );
    state.scene.layers[layerID].holes[holeID].coordinates = [coordinates];
    const holeType = state.scene.layers[layerID].holes[holeID].type;

    if (doorHasWings(holeType)) {
      state = this.updateDoorSweepingPoints(state, holeID).updatedState;
    }
    return { updatedState: state };
  }

  static adjustHolePolygonAfterLineChange(state, layerID, holeID): UpdatedStateObject {
    const layer = getSelectedLayer(state.scene);
    const hole = layer.holes[holeID];
    const { x1, y1, x2, y2 } = SnapSceneUtils.getLineSnapSegmentForHole(state, holeID);

    // Find the closest point from the current hole centroid
    const [hx, hy] = GeometryUtils.getFeatureCentroid(hole.coordinates[0]);
    const { x, y } = GeometryUtils.closestPointFromLineSegment(x1, y1, x2, y2, hx, hy);

    // Use it to recalculate coords
    state = this.recalculateHolePolygon(state, layerID, holeID, [x, y]).updatedState;
    const newHoleProperties = state.scene.layers[layerID].holes[holeID].properties;
    if (!this.areNewPropertiesValid(state, layerID, holeID, newHoleProperties)) {
      state = this.remove(state, layerID, holeID).updatedState;
    }
    return { updatedState: state };
  }

  static setProperties(state, layerID, holeID, properties, enforceValidity = true): UpdatedStateObject {
    if (enforceValidity && !this.areNewPropertiesValid(state, layerID, holeID, properties)) {
      return { updatedState: state };
    }
    state.scene.layers[layerID].holes[holeID].properties = properties;
    state = this.recalculateHolePolygon(state, layerID, holeID).updatedState;

    return { updatedState: state };
  }

  static setJsProperties(state, layerID, holeID, properties): UpdatedStateObject {
    return this.setProperties(state, layerID, holeID, properties);
  }

  static updateProperties(state, layerID, holeID, properties): UpdatedStateObject {
    state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
    const propertiesEntries = Object.entries(properties);

    propertiesEntries.forEach(([k, v]) => {
      const holeHasProperty = state.scene.layers[layerID].holes[holeID].properties.hasOwnProperty(k);
      if (holeHasProperty) {
        state.scene.layers[layerID].holes[holeID].properties = {
          ...state.scene.layers[layerID].holes[holeID].properties,
          [k]: v,
        };
      }
    });
    return { updatedState: state };
  }

  static updateJsProperties(state, layerID, holeID, properties): UpdatedStateObject {
    return this.updateProperties(state, layerID, holeID, properties);
  }

  static setAttributes(state, layerID, holeID, holesAttributes) {
    const hAttr = holesAttributes;
    const clonedState = cloneDeep(state);
    clonedState.scene.layers[layerID].holes[holeID] = { ...clonedState.scene.layers[layerID].holes[holeID], ...hAttr };
    return { updatedState: clonedState };
  }

  static replaceLines(state, holeID, currentLineID, newLineID) {
    const layerID = state.scene.selectedLayer;

    // Erase hole from old line
    const holesOnCurrentLine = state.scene.layers[layerID].lines[currentLineID].holes.filter(ID => ID !== holeID);
    // Add hole to new line
    let holesOnNewLine = state.scene.layers[layerID].lines[newLineID].holes;
    if (!holesOnNewLine.includes(holeID)) holesOnNewLine = holesOnNewLine.concat(holeID);
    state.scene.layers[layerID].lines[currentLineID].holes = holesOnCurrentLine;
    state.scene.layers[layerID].lines[newLineID].holes = holesOnNewLine;
    state.scene.layers[layerID].holes[holeID].line = newLineID;

    return { updatedState: state };
  }

  static changeHoleType(state, holeId, holeType) {
    const selectedLayer = state.scene.selectedLayer;
    const previousHoleType = state.scene.layers[selectedLayer].holes[holeId].type;

    const lineId = state.scene.layers[selectedLayer].holes[holeId].line;
    const coordinates = state.scene.layers[selectedLayer].holes[holeId].coordinates;
    const door_sweeping_points = state.scene.layers[selectedLayer].holes[holeId].door_sweeping_points;
    const currentProperties = state.scene.layers[selectedLayer].holes[holeId].properties;

    const holeAllProperties: HoleType['properties'][] = Object.values(state.catalog.elements[holeType].properties);
    const defaultElementProperties: any = holeAllProperties.map((value: any) => value.defaultValue);
    const [cx, cy] = GeometryUtils.getFeatureCentroid(coordinates[0]);
    const [vertex0, vertex1] = this.getOpeningShortSideMidPoints(state, { x: cx, y: cy }, holeId);
    const defaultSweepingPoints = this.getDoorSweepingPoints(
      vertex0,
      vertex1,
      defaultElementProperties.flip_horizontal,
      defaultElementProperties.flip_vertical
    );

    let sweepingPoints;
    const shouldKeepProperties = doorHasWings(holeType) && doorHasWings(previousHoleType);
    if (shouldKeepProperties) {
      sweepingPoints = door_sweeping_points;
      // previous door has wings, but selected doesn't
    } else if (!doorHasWings(holeType) && doorHasWings(previousHoleType)) {
      sweepingPoints = undefined;
      // selected door has wings, but previous doesn't
    } else if (doorHasWings(holeType) && !doorHasWings(previousHoleType)) {
      sweepingPoints = defaultSweepingPoints;
    }

    const newHole = state.catalog.factoryElement(
      holeType,
      {
        id: holeId,
        name: NameGenerator.generateName('holes', state.catalog.elements[holeType].info.title),
        type: holeType,
        line: lineId,
        coordinates: coordinates,
        door_sweeping_points: sweepingPoints,
        selected: true,
      },
      currentProperties
    );
    state.scene.layers[selectedLayer].holes[holeId] = newHole;

    const isDrawing = state.drawingSupport.drawingStarted;
    if (isDrawing) {
      state.drawingSupport = { ...state.drawingSupport, type: holeType };
    }

    return { updatedState: state };
  }

  static changeHolesType(state, holeIds, holeType): UpdatedStateObject {
    holeIds.forEach(holeId => {
      state = this.changeHoleType(state, holeId, holeType).updatedState;
    });
    return { updatedState: state };
  }
}

export { Hole as default };
