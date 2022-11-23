import { REFERENCE_LINE_POSITION, SNAPS } from '../constants';
import * as GeometryUtils from '../utils/geometry';
import Line from '../class/line';
import { getLineString } from './geometry';
import {
  addLineSegmentSnap,
  addPointSnap,
  addSnapsToCreateParallelLines,
  getItemSnapsAroundAreas,
  getSnapsFromItemCentroid,
  SNAP_POINT,
  SNAP_SEGMENT,
} from './snap';
import { getSelectedLayer } from './state-utils';
import getFastStateObject from './get-fast-state-object';

const { POINT, SEGMENT, COPY_PASTE } = SNAPS;

const RADIUS_ITEMS_CONSIDERED_CM = 150;
export const RADIUS_LINES_CONSIDERED_CM = 50;

function addLineSegmentFromPairOfVertices(snapElements, lineID, v0, v1, radius) {
  const { x: x1, y: y1 } = v0;
  const { x: x2, y: y2 } = v1;
  addLineSegmentSnap(snapElements, x1, y1, x2, y2, radius, SEGMENT.PRIORITY, { lineID });
}

function getVerticesCloseTo(allVertices, radiusInPx, { x, y }) {
  return allVertices.filter(({ x: vx, y: vy }) => {
    const distance = GeometryUtils.pointsDistance(vx, vy, x, y);
    return distance < radiusInPx;
  });
}

/*
 * Calculate snaps that are close to each point of each line in the copy paste selection and returns them.
 * @TODO: Add snaps only for "exterior" line segments, ignoring middle ones.
 */
export function sceneSnapNearestCopyPasteElements(scene, snapMask = {}, selection) {
  if (!snapMask[SNAP_POINT] && !snapMask[SNAP_SEGMENT]) return [];
  const segmentSnaps = {};
  const pointSnaps = {};

  const layer = getSelectedLayer(scene);
  const layerVertices = layer.vertices;

  const copyPastedLines = selection.lines;
  const copyPastedVertices = copyPastedLines.reduce((accum, lineID) => {
    const line = layer.lines[lineID];
    const linePoints = Line.getLineVerticesPoints(line, layerVertices);
    return accum.concat(linePoints);
  }, []);

  const radiusInPx = GeometryUtils.convertCMToPixels(scene.scale, RADIUS_LINES_CONSIDERED_CM);

  const newSnaps = [];
  const allLines = Object.values(layer.lines);
  allLines.forEach(({ id, vertices, auxVertices }) => {
    if (copyPastedLines.includes(id)) return;
    let allVertices = vertices.concat(auxVertices).map(vertexID => layer.vertices[vertexID]);
    allVertices = Object.values(allVertices);
    copyPastedVertices.forEach(([x, y]) => {
      const closeVertices = getVerticesCloseTo(allVertices, radiusInPx, { x, y });
      closeVertices.forEach(({ id, x, y }) => {
        if (pointSnaps[id]) return;
        addPointSnap(newSnaps, x, y, COPY_PASTE.POINT.RADIUS, POINT.PRIORITY, id);
        pointSnaps[id] = true;
      });

      for (let chunkStart = 0; chunkStart < allVertices.length; chunkStart += 2) {
        const desiredVertices = [allVertices.slice(chunkStart, chunkStart + 2)];
        desiredVertices
          .filter(([v0, v1]) => {
            const distance = GeometryUtils.distancePointFromLineSegment(v0.x, v0.y, v1.x, v1.y, x, y);
            return distance < radiusInPx;
          })
          .forEach(([v0, v1]) => {
            if (segmentSnaps[`${v0.id},${v1.id}`]) return;
            addLineSegmentFromPairOfVertices(newSnaps, id, v0, v1, COPY_PASTE.SEGMENT.RADIUS);
            segmentSnaps[`${v0.id},${v1.id}`] = true;
          });
      }
    });
  });
  return newSnaps;
}

export function sceneSnapNearestElementsLine(baseScene, snapElements = [], snapMask = {}, lineID, x, y) {
  const scene = getFastStateObject(baseScene, { returnOriginalObject: true }); // Original object is faster than the state modified
  if (!snapMask[SNAP_POINT] && !snapMask[SNAP_SEGMENT]) return snapElements;

  const { width, height } = scene;

  const radiusInPx = GeometryUtils.convertCMToPixels(scene.scale, RADIUS_LINES_CONSIDERED_CM);

  snapElements = snapElements.filter(snap => snap.metadata.perpendicular);
  const perpendicularSnapsLines = snapElements.map(perpendicularSnap =>
    getLineString([
      [perpendicularSnap.x1, perpendicularSnap.y1],
      [perpendicularSnap.x2, perpendicularSnap.y2],
    ])
  );
  const allLayers = Object.values(scene.layers);
  allLayers.forEach(layer => {
    const allLines = Object.values(layer.lines);
    allLines.forEach(({ id, vertices, auxVertices }) => {
      if (lineID === id) return;
      const allVertices = vertices.concat(auxVertices).map(vertexID => layer.vertices[vertexID]);
      if (snapMask[SNAP_POINT]) {
        const closeVertices = getVerticesCloseTo(allVertices, radiusInPx, { x, y });
        closeVertices.forEach(({ id, x, y }) => addPointSnap(snapElements, x, y, POINT.RADIUS, POINT.PRIORITY, id));
      }

      if (snapMask[SNAP_SEGMENT]) {
        for (let chunkStart = 0; chunkStart < allVertices.length; chunkStart += 2) {
          const desiredVertices = [allVertices.slice(chunkStart, chunkStart + 2)];
          desiredVertices
            .filter(([v0, v1]) => {
              const distance = GeometryUtils.distancePointFromLineSegment(v0.x, v0.y, v1.x, v1.y, x, y);
              return distance < radiusInPx;
            })
            .forEach(([v0, v1]) => addLineSegmentFromPairOfVertices(snapElements, id, v0, v1, SEGMENT.RADIUS));
        }
      }

      const radiusToConsiderParallelLines = radiusInPx * 10; // ~500px (if scale =1)
      const closeVertices = getVerticesCloseTo(allVertices, radiusToConsiderParallelLines, { x, y });
      closeVertices.forEach(({ id, x, y }) =>
        addSnapsToCreateParallelLines(snapElements, x, y, width, height, perpendicularSnapsLines, id)
      );
    });
  });

  snapElements = snapElements.filter(snap => {
    // We cannot filter points for parallel lines because we need to consider far away lines fist and *then* show only the closest snaps
    if (snap.type !== 'point') return true;
    const distance = GeometryUtils.pointsDistance(snap.x, snap.y, x, y);
    return distance < radiusInPx;
  });

  return snapElements;
}

export function sceneSnapItemWithItems(scene, snapElements = [], snapMask = {}, item) {
  const layerID = scene.selectedLayer;
  const items = scene.layers[layerID].items;
  const allItems = Object.values(items);

  const newItemwidthInPixels = GeometryUtils.getElementWidthInPixels(item, scene.scale);
  const newLengthInPixels = GeometryUtils.getElementLengthInPixels(item, scene.scale);
  const radiusInPx = GeometryUtils.convertCMToPixels(scene.scale, RADIUS_ITEMS_CONSIDERED_CM);
  allItems.forEach(otherItem => {
    const { x, y } = otherItem;
    if (item.id != otherItem.id && GeometryUtils.pointsDistance(x, y, item.x, item.y) < radiusInPx) {
      const widthInPixels = GeometryUtils.getElementWidthInPixels(otherItem, scene.scale);
      const lengthInPixels = GeometryUtils.getElementLengthInPixels(otherItem, scene.scale);
      return getSnapsFromItemCentroid(
        snapElements,
        { x, y },
        otherItem.rotation,
        widthInPixels,
        lengthInPixels,
        newItemwidthInPixels,
        newLengthInPixels
      );
    }
  });

  return snapElements;
}

export function sceneSnapAreasBordersItems(scene, snapElements, itemX, itemY, itemDimensions, snapAngle) {
  const layerID = scene.selectedLayer;
  const areas = scene.layers[layerID].areas;
  const allAreas = Object.values(areas);

  // 1. We need to get the Area polygons first, unbuffer them by the dimension selected
  const areasCoords = allAreas.map(a => a.coords);
  let areasCoordsBuffered = [];
  for (const areaCoords of areasCoords) {
    const areaLines = GeometryUtils.getAreaLinesBufferedIfItemInside(
      areaCoords,
      -itemDimensions.length / 2,
      itemX,
      itemY
    );
    if (areaLines) {
      areasCoordsBuffered = areaLines;
      break;
    }
  }
  // 2. Then we build with the coordinates of the areas buffered different lines of snapping
  getItemSnapsAroundAreas(snapElements, areasCoordsBuffered, itemDimensions, snapAngle);

  return snapElements;
}

export function sceneSnapHoleNearestLine(scene, snapElements = [], hole, x, y) {
  const scale = scene.scale;
  const holeLengthInPixels = GeometryUtils.getElementLengthInPixels(hole, scale);

  const layer = getSelectedLayer(scene);
  const { lines, vertices } = layer;
  const allLines = Object.values(lines);

  allLines
    .filter(line => {
      const [v0, v1] = line.vertices.map(vertexID => vertices[vertexID]);
      const lineLength = GeometryUtils.verticesDistance(v0, v1);
      return lineLength >= holeLengthInPixels;
    })
    .forEach(line => {
      const referenceLine = line.properties.referenceLine;
      const lineWidthInPixels = GeometryUtils.getElementWidthInPixels(line, scale);
      const [v0, v1] = (referenceLine === REFERENCE_LINE_POSITION.CENTER
        ? line.vertices
        : line.auxVertices.slice(0, 2)
      ).map(vertexID => {
        const { x, y } = vertices[vertexID];
        return { x, y };
      });

      const radius = lineWidthInPixels / 2;
      const isLineInRadius = GeometryUtils.isPointOnLineSegment(v0.x, v0.y, v1.x, v1.y, x, y, radius);

      if (isLineInRadius) {
        const [x1, y1] = GeometryUtils.getLineOffset(v0.x, v0.y, v1.x, v1.y, holeLengthInPixels / 2);
        const [x2, y2] = GeometryUtils.getLineOffset(v1.x, v1.y, v0.x, v0.y, holeLengthInPixels / 2);
        const snapMetadata = { lineID: line.id };

        addLineSegmentSnap(snapElements, x1, y1, x2, y2, radius, SEGMENT.PRIORITY, snapMetadata);
        addPointSnap(snapElements, x1, y1, radius, POINT.RADIUS, snapMetadata);
        addPointSnap(snapElements, x2, y2, radius, POINT.RADIUS, snapMetadata);
      }
    });

  return snapElements;
}

/* Very similar to the line segment snap above, but hard to generalize so we duplicate the relevant code for now */
export const getLineSnapSegmentForHole = (state, holeID) => {
  const layer = getSelectedLayer(state.scene);
  const hole = layer.holes[holeID];
  const line = layer.lines[hole.line];

  // Take vertices of middle line
  const referenceLine = line.properties.referenceLine;
  const [v0, v1] = (referenceLine === REFERENCE_LINE_POSITION.CENTER
    ? line.vertices
    : line.auxVertices.slice(0, 2)
  ).map(vertexID => {
    const { x, y } = layer.vertices[vertexID];
    return { x, y };
  });

  // Get the line segment that represents the middle line
  const holeLengthInPixels = GeometryUtils.getElementLengthInPixels(hole, state.scene.scale);
  const [x1, y1] = GeometryUtils.getLineOffset(v0.x, v0.y, v1.x, v1.y, holeLengthInPixels / 2);
  const [x2, y2] = GeometryUtils.getLineOffset(v1.x, v1.y, v0.x, v0.y, holeLengthInPixels / 2);

  return { x1, y1, x2, y2 };
};
