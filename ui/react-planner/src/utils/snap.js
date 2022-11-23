import { SNAPS } from '../constants';
import Line from '../class/line';
import * as Geometry from './geometry';
import { getSelectedLayer } from './state-utils';

const { PRIORITY, RADIUS } = SNAPS.PERP_SEGMENT;

export const SNAP_POINT = 'SNAP_POINT';
export const SNAP_SEGMENT = 'SNAP_SEGMENT';

export const SNAP_MASK = {
  SNAP_POINT: true,
  SNAP_SEGMENT: true,
};

const PERP_SNAPS_FROM_ORIGIN_STYLE = { strokeDasharray: '5,5' };

export class PointSnap {
  constructor(json = {}) {
    const x = !isNaN(json.x) ? Geometry.roundCoord(json.x) : -1;
    const y = !isNaN(json.y) ? Geometry.roundCoord(json.y) : -1;
    return {
      ...json,
      type: 'point',
      x,
      y,
      radius: json.radius || 1,
      priority: json.priority || 1,
      metadata: json.metadata || {},
      nearestPoint: this.nearestPoint,
      isNear: this.isNear,
    };
  }

  nearestPoint(x, y) {
    return {
      x: this.x,
      y: this.y,
      distance: Geometry.pointsDistance(this.x, this.y, x, y),
    };
  }
  isNear(x, y, distance) {
    return ~(this.x - x) + 1 < distance && ~(this.y - y) + 1 < distance;
  }
}

export class LineSegmentSnap {
  constructor(json = {}) {
    const x1 = !isNaN(json.x1) ? Geometry.roundCoord(json.x1) : -1;
    const y1 = !isNaN(json.y1) ? Geometry.roundCoord(json.y1) : -1;
    const x2 = !isNaN(json.x2) ? Geometry.roundCoord(json.x2) : -1;
    const y2 = !isNaN(json.y2) ? Geometry.roundCoord(json.y2) : -1;
    return {
      ...json,
      type: 'line-segment',
      x1,
      y1,
      x2,
      y2,
      radius: json.radius || 1,
      priority: json.priority || 1,
      metadata: json.metadata || {},
      nearestPoint: this.nearestPoint,
      isNear: this.isNear,
    };
  }

  nearestPoint(x, y) {
    const { x: closestX, y: closestY } = Geometry.closestPointFromLineSegment(this.x1, this.y1, this.x2, this.y2, x, y);
    return {
      x: Geometry.roundCoord(closestX),
      y: Geometry.roundCoord(closestY),
      distance: Geometry.distancePointFromLineSegment(this.x1, this.y1, this.x2, this.y2, x, y),
    };
  }
  isNear(x, y, distance) {
    return true;
  }
}

/*
 * Check if any of the selection lines snaps with other lines,
 * returning the first nearest snap
 */
export function nearestCopyPasteSnap(state, snapElements, finalDraggingPosition) {
  const { x, y } = finalDraggingPosition;

  const copyPastedLines = state.copyPaste.selection.lines;
  const layer = getSelectedLayer(state.scene);
  const layerVertices = layer.vertices;
  for (const lineID of copyPastedLines) {
    const line = layer.lines[lineID];
    const points = Line.getLineVerticesPoints(line, layerVertices);

    for (const point of points) {
      const snap = nearestSnap(snapElements, point[0], point[1], state.snapMask);
      if (snap) {
        // Translate dragging position the same amount needed to translate this specific snap to this point
        const deltaX = snap.point.x - point[0];
        const deltaY = snap.point.y - point[1];
        const newX = x + deltaX;
        const newY = y + deltaY;
        return { point: { x: newX, y: newY } };
      }
    }
  }
}
export function nearestSnap(snapElements, x, y, snapMask) {
  const filter = {
    point: snapMask[SNAP_POINT],
    'line-segment': snapMask[SNAP_SEGMENT],
  };

  const sortedSnapElements = snapElements
    .filter(el => filter[el.type] && el.isNear(x, y, el.radius))
    .map(snap => {
      return { snap, point: snap.nearestPoint(x, y) };
    })
    .filter(({ snap: { radius }, point: { distance } }) => distance < radius)
    .sort(({ snap: { priority: p1 }, point: { distance: d1 } }, { snap: { priority: p2 }, point: { distance: d2 } }) =>
      p1 === p2 ? (d1 < d2 ? -1 : 1) : p1 > p2 ? -1 : 1
    );
  const nearestSnap = sortedSnapElements[0];
  return nearestSnap;
}

export function addPointSnap(snapElements, x, y, radius, priority, metadata = {}) {
  return snapElements.push(new PointSnap({ x, y, radius, priority, metadata }));
}

export function addLineSegmentSnap(snapElements, x1, y1, x2, y2, radius, priority, metadata) {
  return snapElements.push(new LineSegmentSnap({ x1, y1, x2, y2, radius, priority, metadata }));
}

export function addSnapsToCreateParallelLines(snapElements, x, y, width, height, perpendicularSnapsLines, id) {
  const verticalLineTop = Geometry.getLineString([
    [x, y],
    [x, height],
  ]);
  const verticalLineBottom = Geometry.getLineString([
    [x, y],
    [x, 0],
  ]);

  const horizontalLineRight = Geometry.getLineString([
    [x, y],
    [width, y],
  ]);
  const horizontalLineLeft = Geometry.getLineString([
    [x, y],
    [0, y],
  ]);
  perpendicularSnapsLines.forEach(perpendicularSnap => {
    for (const line of [verticalLineTop, verticalLineBottom, horizontalLineLeft, horizontalLineRight]) {
      const intersection = Geometry.lineIntersect(line, perpendicularSnap);
      if (intersection.features.length) {
        intersection.features.forEach(point => {
          const [x, y] = point.geometry.coordinates;
          addPointSnap(snapElements, x, y, SNAPS.POINT.RADIUS, SNAPS.POINT.PRIORITY, id);
        });
      }
    }
  });
}

function getPerpendicularSnapsFromLine(
  scene,
  snapElements,
  startingPoint,
  intersectingLine,
  options = { sameAxis: false }
) {
  const lineToRotate = Geometry.extendLineToCoverScene(intersectingLine, scene.width, scene.height);

  const pivotPoint = [startingPoint.x, startingPoint.y];

  const perpendicularLine1 = Geometry.rotateFeature(lineToRotate, 90, pivotPoint);
  const perpendicularLine2 = Geometry.rotateFeature(lineToRotate, -90, pivotPoint);
  const paralellLine1 = Geometry.rotateFeature(lineToRotate, 180, pivotPoint);
  const paralellLine2 = Geometry.rotateFeature(lineToRotate, -180, pivotPoint);

  const snapLines = options.sameAxis
    ? [paralellLine1, paralellLine2]
    : [perpendicularLine1, perpendicularLine2, paralellLine1, paralellLine2];

  for (const line of snapLines) {
    const [[x1, y1], [x2, y2]] = Geometry.getFeatureCoords(line);
    addLineSegmentSnap(snapElements, x1, y1, x2, y2, RADIUS, PRIORITY, { perpendicular: true });
  }

  return snapElements;
}

// @TODO: Rewrite using turf.js as with the method above
function getPerpendicularSnapsFromOrigin(scene, snapElements, { x, y }) {
  const { width, height } = scene;

  const snapMetadata = {
    style: PERP_SNAPS_FROM_ORIGIN_STYLE,
    perpendicular: true,
  };

  // Create vertical + horizontal based on the rotated points above
  addLineSegmentSnap(snapElements, x, y, x, height, RADIUS, PRIORITY, snapMetadata);
  addLineSegmentSnap(snapElements, x, y, x, 0, RADIUS, PRIORITY, snapMetadata);

  addLineSegmentSnap(snapElements, x, y, width, y, RADIUS, PRIORITY, snapMetadata);
  addLineSegmentSnap(snapElements, x, y, 0, y, RADIUS, PRIORITY, snapMetadata);
  return snapElements;
}

export function getSnapsFromItemCentroid(
  snapElements,
  { x, y },
  SnappingAngle,
  widthInPixels,
  lengthInPixels,
  newItemwidthInPixels,
  newLengthInPixels
) {
  // vertical lines
  const { x: x1, y: y1 } = Geometry.PointOnLineGivenAngleAndPoint(
    x,
    y,
    SnappingAngle + 90,
    lengthInPixels / 2 + newLengthInPixels / 2
  );
  const { x: x2, y: y2 } = Geometry.PointOnLineGivenAngleAndPoint(
    x,
    y,
    SnappingAngle + 270,
    lengthInPixels / 2 + newLengthInPixels / 2
  );

  // horizontal lines
  const { x: x3, y: y3 } = Geometry.PointOnLineGivenAngleAndPoint(
    x,
    y,
    SnappingAngle,
    widthInPixels / 2 + newItemwidthInPixels / 2
  );
  const { x: x4, y: y4 } = Geometry.PointOnLineGivenAngleAndPoint(
    x,
    y,
    SnappingAngle + 180,
    widthInPixels / 2 + newItemwidthInPixels / 2
  );

  // vertical lines
  addPointSnap(snapElements, x1, y1, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY, { SnappingAngle: SnappingAngle });
  addPointSnap(snapElements, x2, y2, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY, { SnappingAngle: SnappingAngle });
  // horizontal lines
  addPointSnap(snapElements, x3, y3, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY, { SnappingAngle: SnappingAngle });
  addPointSnap(snapElements, x4, y4, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY, { SnappingAngle: SnappingAngle });

  return snapElements;
}

export function addSnapLinesSameAxis(scene, startingPoint, layer) {
  const snapElements = [];
  const intersectingLine = Geometry.getIntersectingLineString(
    layer,
    { x: startingPoint.x, y: startingPoint.y },
    { checkAllVertices: false } // Otherwise we could get perpendicular intersecting lines instead of parallel ones
  );
  if (!intersectingLine) return [];
  return getPerpendicularSnapsFromLine(scene, snapElements, startingPoint, intersectingLine, { sameAxis: true });
}

export function addPerpendicularSnapLines(scene, snapElements, startingPoint, layer) {
  const intersectingLine = Geometry.getIntersectingLineString(layer, { x: startingPoint.x, y: startingPoint.y });
  let snaps = [];

  if (intersectingLine) {
    snaps = snaps.concat(getPerpendicularSnapsFromLine(scene, snapElements, startingPoint, intersectingLine));
  }
  return snaps.concat(getPerpendicularSnapsFromOrigin(scene, snapElements, startingPoint));
}

function getLineSnapsForItem(areasCoords, widthLengthDiff) {
  const isProportionalItem = widthLengthDiff === 0;
  let lines = Geometry.getAllAreasLinesFromArea(areasCoords);
  if (!isProportionalItem) {
    const halfWidthLengthDiff = Math.floor(widthLengthDiff / 2);
    lines = lines.map(line => {
      let [[x1, y1], [x2, y2]] = line;
      const angle = Geometry.angleBetweenTwoPointsAndOrigin(x1, y1, x2, y2);
      const vertexA = Geometry.PointOnLineGivenAngleAndPoint(x1, y1, angle, halfWidthLengthDiff);
      const vertexB = Geometry.PointOnLineGivenAngleAndPoint(x2, y2, angle, -halfWidthLengthDiff);
      [x1, y1] = [vertexA.x, vertexA.y];
      [x2, y2] = [vertexB.x, vertexB.y];

      return [
        [x1, y1],
        [x2, y2],
      ];
    });
  }

  return lines;
}

export function getItemSnapsAroundAreas(snapElements, areasCoords, { width, length }, snapAngle) {
  const widthLengthDiff = Math.ceil(width - length);
  const isProportionalItem = widthLengthDiff === 0;
  const lines = getLineSnapsForItem(areasCoords, widthLengthDiff);

  lines.forEach(line => {
    const vertexA = { x: line[0][0], y: line[0][1] };
    const vertexB = { x: line[1][0], y: line[1][1] };
    const lineAngle = Geometry.angleBetweenTwoPointsAndOrigin(vertexB.x, vertexB.y, vertexA.x, vertexA.y);
    const metadata = {
      SnappingAngle: lineAngle + snapAngle,
    };
    addLineSegmentSnap(
      snapElements,
      vertexA.x,
      vertexA.y,
      vertexB.x,
      vertexB.y,
      SNAPS.ITEM.RADIUS,
      SNAPS.ITEM.AREAS_PRIORITY,
      metadata
      // Use here the inverted angle of the wall so that is always facing the room
    );
    // For the vertices of each line, we also add a snapping point with higher priority, so in the corners
    // we can snap correctly
    if (!isProportionalItem) {
      addPointSnap(snapElements, vertexA.x, vertexA.y, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY);
    }
    addPointSnap(snapElements, vertexB.x, vertexB.y, SNAPS.ITEM.RADIUS, SNAPS.ITEM.PRIORITY);
  });

  return snapElements;
}
