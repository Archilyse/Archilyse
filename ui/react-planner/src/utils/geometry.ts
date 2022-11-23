import areapolygon from 'area-polygon';
import polygonClipping from 'polygon-clipping';
import polylabel from 'polylabel';

/* eslint-disable */
import {
  // @ts-ignore https://github.com/Turfjs/turf/pull/2157, not yet released
  booleanIntersects as TurfBooleanIntersects,
  simplify as turfSimplify,
} from '@turf/turf';
import {
  convex,
  featureCollection,
  point as turfPoint,
  bboxPolygon,
  getCoords,
  area as turfArea,
  toWgs84,
  polygon as turfPolygon,
  intersect as turfIntersect,
  difference,
  bbox,
  centroid,
  transformScale,
  toMercator,
  multiPolygon,
  buffer,
  transformRotate,
  lineString as turfLineString,
  booleanPointOnLine,
  booleanWithin as turfBooleanWithin,
  booleanEqual as turfBooleanEqual,
  lineIntersect as turfLineIntersect,
  pointToLineDistance as turfPointToLineDistance,
  polygonToLine as turfPolygonToLine,
} from '@turf/turf';
/* eslint-enable */
import { parse as geoJSONRoundFeature } from 'geojson-precision';
import {
  BBox,
  Feature,
  FeatureCollection,
  Geometry,
  LineString,
  MultiLineString,
  MultiPolygon,
  Point,
  Polygon,
  Position,
} from 'geojson';
import { Hole, LineSegment, PolygonEdge, Selection, XYCoord } from '../types';
import {
  BUFFER_RADIUS_KM,
  EPSILON,
  GEOJSON_FEATURE_TYPES,
  REFERENCE_LINE_POSITION,
  VERTEX_ROUNDING_PRECISION,
} from '../constants';
import { fAbs, toFixedFloat } from './math';
import cloneDeep from './clone-deep';
import hasCopyPasteBeenDragged from './has-copy-paste-been-dragged';

const { CENTER, INSIDE_FACE, OUTSIDE_FACE } = REFERENCE_LINE_POSITION;

const UNION_POLYGON_PRECISION = 8; // https://gis.stackexchange.com/a/8674

export const radToDeg = angleInRad => (angleInRad * 180) / Math.PI;

export const toXYCoords = (feature: Feature<Geometry>): Feature<Geometry> => toMercator(feature);
export function toLatLng(feature: Feature<Geometry>, mutate = false): Feature<Geometry> {
  return toWgs84(feature, { mutate: mutate });
}

export function compareVertices(v0, v1) {
  return v0.x === v1.x ? v0.y - v1.y : v0.x - v1.x;
}

export function compareCoords(p0: Position, p1: Position) {
  const [x0, y0] = p0;
  const [x1, y1] = p1;
  return x0 === x1 ? y0 - y1 : x0 - x1;
}

export function orderCoords(coords: Position[]) {
  return coords.sort(compareCoords);
}

export function minVertex(v0, v1) {
  return compareVertices(v0, v1) > 0 ? v1 : v0;
}

export function maxVertex(v0, v1) {
  return compareVertices(v0, v1) > 0 ? v0 : v1;
}

export function orderVertices(vertices) {
  return vertices.sort(compareVertices);
}

export function pointsDistance(x0, y0, x1, y1) {
  const diff_x = x0 - x1;
  const diff_y = y0 - y1;

  return Math.sqrt(diff_x * diff_x + diff_y * diff_y);
}

export function verticesDistance(v1, v2) {
  const { x: x0, y: y0 } = v1;
  const { x: x1, y: y1 } = v2;

  return pointsDistance(x0, y0, x1, y1);
}

export function booleanIntersects(feature1: Feature<Geometry>, feature2: Feature<Geometry>) {
  return TurfBooleanIntersects(feature1, feature2);
}

export function intersect(feature1: Feature<Polygon | MultiPolygon>, feature2: Feature<Polygon | MultiPolygon>) {
  return turfIntersect(feature1, feature2);
}

export function booleanWithin(feature1: Feature<Geometry>, feature2: Feature<Geometry>) {
  return turfBooleanWithin(feature1, feature2);
}

export function booleanEqual(feature1: Feature<Geometry>, feature2: Feature<Geometry>): boolean {
  return turfBooleanEqual(feature1, feature2);
}

export function distancePointFromLineSegment(x1, y1, x2, y2, xp, yp) {
  const line = toLatLng(
    getLineString([
      [x1, y1],
      [x2, y2],
    ])
  ) as Feature<LineString>;
  const point = toLatLng(getPoint(xp, yp)) as Feature<Point>;
  return turfPointToLineDistance(point, line, { units: 'meters' });
}

// TODO: DEPRECATED, replace the usages of this with `isPointOnLine` below and erase this method
export function isPointOnLineSegment(x1, y1, x2, y2, xp, yp, maxDistance = EPSILON) {
  return distancePointFromLineSegment(x1, y1, x2, y2, xp, yp) <= maxDistance;
}

// TODO: replace with 'nearestPointOnLine' from turf.js
export function closestPointFromLineSegment(x1, y1, x2, y2, xp, yp) {
  if (x1 === x2) return { x: x1, y: yp };
  if (y1 === y2) return { x: xp, y: y1 };
  const m = (y2 - y1) / (x2 - x1);
  const q = y1 - m * x1;

  const mi = -1 / m;
  const qi = yp - mi * xp;

  const x = (qi - q) / (m - mi);
  const y = m * x + q;

  return { x, y };
}

export function getLineOffset(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  distance: number,
  precision = 6
): number[] {
  const rad = angleBetweenTwoPoints(x1, y1, x2, y2);
  return [
    toFixedFloat(x1 + Math.cos(rad) * distance, precision),
    toFixedFloat(y1 + Math.sin(rad) * distance, precision),
  ];
}

export function pointPositionOnLineSegment(x1, y1, x2, y2, xp, yp) {
  const length = pointsDistance(x1, y1, x2, y2);
  const distance = pointsDistance(x1, y1, xp, yp);

  let offset = distance / length;
  if (x1 > x2) offset = mapRange(offset, 0, 1, 1, 0);

  return offset;
}

export function mapRange(value, low1, high1, low2, high2) {
  return low2 + ((high2 - low2) * (value - low1)) / (high1 - low1);
}

export function angleBetweenTwoPointsAndOrigin(x1, y1, x2, y2) {
  return radToDeg(-Math.atan2(y1 - y2, x2 - x1));
}

export function angleBetweenTwoPoints(x1, y1, x2, y2) {
  return Math.atan2(y2 - y1, x2 - x1);
}

export function absAngleBetweenTwoPoints(x1, y1, x2, y2) {
  return Math.atan2(Math.abs(y2 - y1), Math.abs(x2 - x1));
}

export function sameCoords(c0: Position, c1: Position, epsilon = EPSILON) {
  const [x0, y0] = c0;
  const [x1, y1] = c1;
  return Math.abs(x0 - x1) <= epsilon && Math.abs(y0 - y1) <= epsilon;
}

export function samePoints({ x: x1, y: y1 }, { x: x2, y: y2 }, epsilon = EPSILON) {
  return fAbs(x1 - x2) <= epsilon && fAbs(y1 - y2) <= epsilon;
}

export function getPolygonEdges(polygon: Feature<Polygon>): PolygonEdge[] {
  const edges = [];
  const lineString = polygonToLine(polygon) as Feature<LineString>;
  const linePoints = getFeatureCoords(lineString) as Position[];

  for (let i = 1; i < linePoints.length; ++i) {
    const [x1, y1] = linePoints[i - 1];
    const [x2, y2] = linePoints[i];
    const length = pointsDistance(x1, y1, x2, y2);
    edges.push({
      points: [
        { x: x1, y: y1 },
        { x: x2, y: y2 },
      ],
      length,
    });
  }
  return edges;
}

export function getTwoShortestSidesFromPolygon(polygon: Feature<Polygon>): PolygonEdge[] {
  const edges = getPolygonEdges(polygon);
  return edges.sort((a, b) => a.length - b.length).slice(0, 2);
}

export function lineHasZeroLength(v0, v1) {
  // @TODO: Use this in the future: http://turfjs.org/docs/#length
  return verticesDistance(v0, v1) === 0 || samePoints(v0, v1) || v0.id === v1.id;
}
/** @description Extend line based on coordinates and new line length
 *  @param {number} x1 Vertex 1 x
 *  @param {number} y1 Vertex 1 y
 *  @param {number} x2 Vertex 2 x
 *  @param {number} y2 Vertex 2 y
 *  @param {number} newDistance New line length
 *  @return {object}
 **/
export function extendLine(x1, y1, x2, y2, newDistance, precision = 6) {
  const rad = angleBetweenTwoPoints(x1, y1, x2, y2);
  return {
    x: toFixedFloat(x1 + Math.cos(rad) * newDistance, precision),
    y: toFixedFloat(y1 + Math.sin(rad) * newDistance, precision),
  };
}

export function roundCoord(coord) {
  return toFixedFloat(coord, VERTEX_ROUNDING_PRECISION);
}

// Gets the new hole offset position after changing the vertices of a line
export function getHolePositionAfterChangingLine(vertex1, vertex2, previousOffset) {
  const lineLength = pointsDistance(vertex1.x, vertex1.y, vertex2.x, vertex2.y);

  const orderedVertices = orderVertices([vertex1, vertex2]);

  const offsetPosition = extendLine(
    orderedVertices[0].x,
    orderedVertices[0].y,
    orderedVertices[1].x,
    orderedVertices[1].y,
    lineLength * previousOffset
  );
  return offsetPosition;
}

export function cosWithThreshold(alpha, threshold) {
  const cos = Math.cos(alpha);
  return cos < threshold ? 0 : cos;
}

export function sinWithThreshold(alpha, threshold) {
  const sin = Math.sin(alpha);
  return sin < threshold ? 0 : sin;
}

export function midPoint(x1, y1, x2, y2) {
  return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 };
}

export function verticesMidPoint(verticesArray) {
  const res = verticesArray.reduce(
    (incr, vertex) => {
      return { x: incr.x + vertex.x, y: incr.y + vertex.y };
    },
    { x: 0, y: 0 }
  );
  return { x: res.x / verticesArray.length, y: res.y / verticesArray.length };
}

export function rotatePointAroundPoint(px, py, ox, oy, theta) {
  const thetaRad = (theta * Math.PI) / 180;

  const cos = Math.cos(thetaRad);
  const sin = Math.sin(thetaRad);

  const deltaX = px - ox;
  const deltaY = py - oy;

  return {
    x: cos * deltaX - sin * deltaY + ox,
    y: sin * deltaX + cos * deltaY + oy,
  };
}

export function PointOnLineGivenAngleAndPoint(x, y, angle, offset) {
  const thetaRad = (angle * Math.PI) / 180;
  const cos = Math.cos(thetaRad);
  const sin = Math.sin(thetaRad);

  const newX = x + cos * offset;
  const newY = y + sin * offset;
  return { x: newX, y: newY };
}

export function isVerticalLine(x1, x2, y1, y2) {
  const length = pointsDistance(x1, y1, x2, y2);
  const isVertical = x2 - x1 < length;
  return isVertical;
}

export function isHorizontalLine(x1, x2, y1, y2) {
  return !isVerticalLine(x1, x2, y1, y2);
}

export function getOffsetsFromReferenceLine(referenceLine, width): number[] {
  if (referenceLine === CENTER) return [-width / 2, width / 2];
  if (referenceLine === INSIDE_FACE) return [-width / 2, -width];
  if (referenceLine === OUTSIDE_FACE) return [width / 2, width];
  return [0, 0];
}

export function getOffsetFromCenter(referenceLine, width): number {
  if (referenceLine === CENTER) return 0;
  if (referenceLine === INSIDE_FACE) return -width / 2;
  if (referenceLine === OUTSIDE_FACE) return width / 2;
  return 0;
}

export function getOuterPolygonPointsFromReferenceLine(
  referenceLinePoints,
  referenceLine: string,
  scaledWidth: number
) {
  if (referenceLine == REFERENCE_LINE_POSITION.CENTER) {
    const [offset1, offset2] = getOffsetsFromReferenceLine(referenceLine, scaledWidth);
    const [[x1, y1], [x2, y2]] = getParallelLinePointsFromOffset(referenceLinePoints, offset1);
    const [[x3, y3], [x4, y4]] = getParallelLinePointsFromOffset(referenceLinePoints, offset2);
    return [
      [x1, y1],
      [x2, y2],
      [x4, y4],
      [x3, y3],
      [x1, y1],
    ];
  } else {
    const offset = getOffsetsFromReferenceLine(referenceLine, scaledWidth)[1];
    const [[x1, y1], [x2, y2]] = getParallelLinePointsFromOffset(referenceLinePoints, offset);
    return [
      [x1, y1],
      [x2, y2],
      [referenceLinePoints.x2, referenceLinePoints.y2],
      [referenceLinePoints.x1, referenceLinePoints.y1],
      [x1, y1],
    ];
  }
}

export function getOpeningPolygonPointsFromSnap(
  { x, y },
  openingLengthInPixels: number,
  lineWidthInPixels: number,
  tetha: number
): number[][] {
  const width = openingLengthInPixels / 2;
  const height = lineWidthInPixels / 2;

  const { x: x1, y: y1 } = rotatePointAroundPoint(x - width, y + height, x, y, tetha);
  const { x: x2, y: y2 } = rotatePointAroundPoint(x + width, y + height, x, y, tetha);
  const { x: x3, y: y3 } = rotatePointAroundPoint(x + width, y - height, x, y, tetha);
  const { x: x4, y: y4 } = rotatePointAroundPoint(x - width, y - height, x, y, tetha);

  return [
    [x1, y1],
    [x2, y2],
    [x3, y3],
    [x4, y4],
    [x1, y1],
  ];
}

export function getUniquePolygonPoints(coordinates: Hole['coordinates']) {
  const [coords] = cloneDeep(coordinates);
  return coords.reduce((acc: Position[], coord: Position) => {
    if (acc.every((c: Position) => !sameCoords(c, coord))) {
      acc.push(coord);
    }
    return acc;
  }, []);
}

export function getParallelLinePointsFromOffset({ x1, x2, y1, y2 }, offset) {
  const L = pointsDistance(x1, y1, x2, y2);

  const [{ x: x1p, y: y1p }, { x: x2p, y: y2p }] = orderVertices([
    { x: x1 + (offset * (y2 - y1)) / L, y: y1 + (offset * (x1 - x2)) / L },
    { x: x2 + (offset * (y2 - y1)) / L, y: y2 + (offset * (x1 - x2)) / L },
  ]);

  return [
    [x1p, y1p],
    [x2p, y2p],
  ];
}

export function getLinePointsFromReferenceLine({ x1, x2, y1, y2 }, referenceLine, width) {
  const points = { x1, x2, y1, y2 };
  const offset = getOffsetFromCenter(referenceLine, width);
  return getParallelLinePointsFromOffset(points, offset);
}

export function getItemPolygon(x: number, y: number, angle: number, itemWidthInPx: number, itemLengthInPx: number) {
  const minX = x - itemWidthInPx / 2;
  const minY = y - itemLengthInPx / 2;
  const maxX = x + itemWidthInPx / 2;
  const maxY = y + itemLengthInPx / 2;
  const itemPolygon = bboxPolygon([minX, minY, maxX, maxY]);
  return rotateFeature(itemPolygon, angle, [x, y]);
}

// @TODO: Replace usages of this for the turf version
export function getScaleAreaSize(points) {
  const polygonArray = points.map(p => [p.x, p.y]);
  return areapolygon(polygonArray, false) / 10000; // m2
}

export function getLinearScale(scaleFactor) {
  return Math.sqrt(scaleFactor);
}

export function convertCMToPixels(scaleFactor, centimeters) {
  return centimeters / getLinearScale(scaleFactor);
}

export function convertSqCMtoSQM(sqCentimeters) {
  const sqCMTosqM = 1e-4;
  return sqCentimeters * sqCMTosqM;
}

export function convertPixelsToCMs(scaleFactor, pixels) {
  return pixels * getLinearScale(scaleFactor);
}

export function getLineDistance(points) {
  const { x: x1, y: y1 } = points[0];
  const { x: x2, y: y2 } = points[1];
  const distanceInCm = pointsDistance(x1, y1, x2, y2);
  return distanceInCm / 100; // meters
}

export function isLine(points: XYCoord[]) {
  return points.length === 2;
}

export function isPolygon(points: XYCoord[]) {
  return points.length > 4; // More than two lines
}

export function getConvexHull(points: Position[]): Feature<Polygon> {
  const geoPoints = Object.values(points).map(point => turfPoint(point));
  const convexHull = convex(featureCollection(geoPoints)) as Feature<Polygon>;
  return convexHull;
}

export function getSimplifiedPolygon(linePolygon: Feature<Polygon>): Feature<Polygon> {
  const [originalCoords] = getFeatureCoords(linePolygon) as Position[][];
  const convexHull = getConvexHull(originalCoords);
  return turfSimplify(convexHull, { tolerance: 0.01, highQuality: true });
}

export function getAreaLinesBufferedIfItemInside(areaCoords, bufferValue, itemX, itemY) {
  const areaExterior = toLatLng(turfPolygon(areaCoords));
  const itemInArea = TurfBooleanIntersects(areaExterior, toLatLng(getPoint(itemX, itemY)));
  if (itemInArea) {
    const coords = [];
    const exteriorBuffered = buffer(areaExterior, bufferValue, { units: 'meters' });
    if (!exteriorBuffered) return null;
    coords.push(getFeatureCoords(toXYCoords(exteriorBuffered) as Feature<Polygon>));
    if (areaCoords.length > 1) {
      for (let i = 1; i < areaCoords.length; i++) {
        const latLngIntPolygon = toLatLng(turfPolygon([areaCoords[i]]));
        const interiorBuffered = buffer(latLngIntPolygon, -bufferValue, { units: 'meters' });
        if (interiorBuffered) {
          coords.push(getFeatureCoords(toXYCoords(interiorBuffered) as Feature<Polygon>));
        }
      }
    }
    return coords;
  }
  return null;
}

export function bufferTurfFeature(polygon: Feature<Geometry>, bufferRadius: number) {
  const latLngPolygon = toLatLng(polygon);
  return buffer(latLngPolygon, bufferRadius, { units: 'kilometers' });
}

export function roundFeature(feature: Feature<Geometry>, precision = VERTEX_ROUNDING_PRECISION) {
  return geoJSONRoundFeature(feature, precision);
}

export function preprocessFeatureForUnion(feature) {
  // Buffer polygon so the below union in joinPolygons considers that cases such as two polygons with the same vertex are intersecting
  const bufferedPolygon = bufferTurfFeature(feature, BUFFER_RADIUS_KM);
  // We need to round all coords, by default the standard precision is too high (subatomic)
  // https://github.com/mfogel/polygon-clipping/issues/101 && https://github.com/Turfjs/turf/issues/357#issuecomment-213914200
  const roundedFeature = roundFeature(bufferedPolygon, UNION_POLYGON_PRECISION);
  return getCoords(roundedFeature);
}

export function joinPolygons(preprocessedPolygonCoords: any[]): Feature<Polygon | MultiPolygon> {
  const unioned = polygonClipping.union(preprocessedPolygonCoords); // https://github.com/Turfjs/turf/issues/2092
  if (unioned.length === 0) return null;
  if (unioned.length === 1) return toXYCoords(turfPolygon(unioned[0])) as Feature<Polygon>;
  else return toXYCoords(multiPolygon(unioned)) as Feature<MultiPolygon>;
}

/** Scale feature by a given factor
 *  Notice we need to pass the feature first to lat/lng, so turf can
 *  properly scale it and then again to our xy system
 * @TODO: Check if is safe to add `mutate:true` as default option to make it faster
 */
export function scaleFeature(feature: Feature, factor = 3, options = undefined): Feature {
  const latLngFeature = toLatLng(feature) as Feature<Polygon | MultiPolygon>;
  const scaledLatLng = transformScale(latLngFeature, factor, options);
  const scaledFeature = toXYCoords(scaledLatLng);
  return scaledFeature;
}

export function rotateFeature(feature: Feature, degrees, pivot): Feature {
  const latLngFeature = toLatLng(feature) as Feature<Polygon | MultiPolygon | LineString | Point>;
  const pointToRotate = toLatLng(getPoint(pivot[0], pivot[1])) as Feature<Point>;
  const coords = getFeatureCoords(pointToRotate) as Position;
  const rotatedFeature = transformRotate(latLngFeature, -degrees, { pivot: coords, mutate: true });
  return toXYCoords(rotatedFeature);
}

export function getBoundingBox(feature: Feature): BBox {
  return bbox(feature);
}

export function getPolygonFromBoundingBox(bbox: BBox): Feature<Polygon> {
  return bboxPolygon(bbox);
}

export function getDifference(
  feature1: Feature<Polygon | MultiPolygon>,
  feature2: Feature<Polygon | MultiPolygon>
): Feature<Polygon | MultiPolygon> {
  return difference(feature1, feature2);
}

export function getMultiPolygon(coordinates: Position[][][]): Feature<MultiPolygon> {
  return multiPolygon(coordinates);
}

export function getLineString(points: Position[]): Feature<LineString> {
  return turfLineString(points);
}

export function getPoint(x: number, y: number): Feature<Point> {
  return turfPoint([x, y]);
}

export function getFeatureCoords(
  feature: Feature<Polygon | MultiPolygon | LineString | Point>
): Position[][] | Position[] | Position {
  return getCoords(feature);
}

export function getFeatureCentroid(featureCoordinates: Position[]): Position | Position[] {
  if (!featureCoordinates.length) throw Error('Passed empty feature coordinate error to get centroid.');
  const feature = getConvexHull(featureCoordinates);
  return getFeatureCoords(centroid(feature)) as Position | Position[];
}

export function findBiggestPolygonInMultiPolygon(multiPolygon: Feature<MultiPolygon>): Feature<Polygon> {
  // If here we don't have a multipolygon it means the areas are not closed
  if (multiPolygon.geometry.type !== GEOJSON_FEATURE_TYPES.MULTIPOLYGON) return null;
  let maxAreaPolygon;
  let maxArea = 0;

  for (const poly of multiPolygon.geometry.coordinates) {
    const polygon = turfPolygon(poly);
    const area = turfArea(toLatLng(polygon));
    if (area > maxArea) {
      maxArea = area;
      maxAreaPolygon = polygon;
    }
  }
  return maxAreaPolygon;
}

export function getAreaPolygon(area) {
  const polygonCoords = area.coords;
  return turfPolygon(polygonCoords);
}

export function getFeatureSize(polygon) {
  return turfArea(toLatLng(polygon));
}

export function getAreaSizeInPixels(area) {
  return getFeatureSize(getAreaPolygon(area));
}

export function getAreaSizeFromScale(area, planScale) {
  const areaSizeinPixels = getAreaSizeInPixels(area);
  return (convertSqCMtoSQM(areaSizeinPixels) * planScale).toFixed(2);
}

export function getAreaCenter(area) {
  const polygonCoords = area.coords;
  return polylabel(polygonCoords, 1.0);
}
export const getStartingLineFromPoint = (layer, { x, y }) => {
  const allLines = Object.values(layer.lines) as any[];
  return allLines.find(line => {
    const [linePrimaryVertex, lineSecondaryVertex] = line.vertices;
    const v0 = layer.vertices[linePrimaryVertex];
    const v1 = layer.vertices[lineSecondaryVertex];
    const [a0, a1, a2, a3] = line.auxVertices.map(vertexID => layer.vertices[vertexID]);

    const verticesToCheck =
      line.auxVertices.length > 0
        ? [
            [v0, v1],
            [a0, a1],
            [a2, a3],
          ]
        : [[v0, v1]];
    return verticesToCheck.some(pair => {
      const [v0, v1] = pair;
      const point = { x, y };
      const line = { x1: v0.x, y1: v0.y, x2: v1.x, y2: v1.y };
      return isPointOnLine(point, line);
    });
  });
};

export const getIntersectingLineString = (
  layer,
  { x, y },
  options = { checkAllVertices: true }
): Feature<LineString> => {
  const lines = Object.values(layer.lines) as any;

  for (const line of lines) {
    const [linePrimaryVertex, lineSecondaryVertex] = line.vertices;
    const m0 = layer.vertices[linePrimaryVertex];
    const m1 = layer.vertices[lineSecondaryVertex];

    const [a0, a1, a2, a3] = line.auxVertices.map(vertexID => layer.vertices[vertexID]);

    const verticesToCheck =
      line.auxVertices.length > 0 && options.checkAllVertices
        ? [
            [m0, m1],
            [a0, a1],
            [a2, a3],
          ]
        : [[m0, m1]];
    for (const pair of verticesToCheck) {
      const [v0, v1] = pair;
      const point = { x, y };
      const line = { x1: v0.x, y1: v0.y, x2: v1.x, y2: v1.y };
      const intersects = isPointOnLine(point, line);
      if (intersects) {
        return getLineString([
          [line.x1, line.y1],
          [line.x2, line.y2],
        ]);
      }
    }
  }
  return null;
};

// @TODO: Express with a type that this returns lat lng
export function preprocessForOperation(feature: Feature<Geometry>): Feature<Geometry> {
  const roundedFeature = roundFeature(feature, VERTEX_ROUNDING_PRECISION);
  return toLatLng(roundedFeature);
}

export const getPostProcessableIntersectingLines = (layer, lineID: string) => {
  const line = layer.lines[lineID];
  const [coordinates] = line.coordinates;
  const selectedLineHull = preprocessForOperation(getConvexHull(coordinates)) as Feature<Polygon>;
  const allLines = Object.values(layer.lines) as any;
  const intersectingLines = allLines.filter(line => {
    if (lineID && lineID === line.id) return false;
    const [coordinates] = line.coordinates;
    const otherLineHull = preprocessForOperation(getConvexHull(coordinates)) as Feature<Polygon>;
    return booleanIntersects(selectedLineHull, otherLineHull) && turfIntersect(selectedLineHull, otherLineHull);
  });

  return intersectingLines;
};

export function isPointOnLine({ x, y }, { x1, y1, x2, y2 }, epsilon: number = 10 ** -10): boolean {
  // The epsilon number is the degree of precision in lat/lon terms, which is 110 microns tolerance
  // reducing this to -8 means we accept a tolerance of 1.1mm
  // This is a bit more complicated when we use pixel based coordinates, because each pixel represents 1 meter.
  const point = toLatLng(getPoint(x, y)) as Feature<Point>;
  const lineString = getLineString([
    [x1, y1],
    [x2, y2],
  ]);
  return booleanPointOnLine(point, toLatLng(lineString) as Feature<LineString>, { epsilon: epsilon });
}

export function getElementWidthInPixels(element, scale) {
  const elementWidth = element.properties.width.value;
  return convertCMToPixels(scale, elementWidth);
}

export function getElementLengthInPixels(element, scale) {
  const elementLength = element.properties.length.value;
  return convertCMToPixels(scale, elementLength);
}

export function getAllAreasLinesFromArea(areasCoords) {
  const areaLines = [];
  areasCoords.forEach(innerOuter => {
    innerOuter.forEach(coords => {
      for (let i = 1; i < coords.length; i++) {
        const [x1, y1] = coords[i - 1];
        const [x2, y2] = coords[i];
        areaLines.push([
          [x1, y1],
          [x2, y2],
        ]);
      }
    });
  });
  return areaLines;
}

export function createPolygon(coords: Position[][]): Feature<Polygon> {
  return turfPolygon(coords);
}

export function extendLineToCoverScene(
  line: Feature<LineString>,
  sceneWidth: number,
  sceneHeight: number
): Feature<LineString> {
  const [[x1, y1], [x2, y2]] = getFeatureCoords(line) as Position[];
  const lineLength = pointsDistance(x1, y1, x2, y2);
  const sceneLength = pointsDistance(0, 0, sceneWidth, sceneHeight);
  const factorToScale = Math.round(sceneLength / lineLength);

  // Depend on where the line is drawn, the factor as is can not be enough so as hack we multiply it per two
  return scaleFeature(line, factorToScale * 2, { mutate: true }) as Feature<LineString>; // 'mutate' makes it faster https://turfjs.org/docs/#transformScale
}

export function lineIntersect(line1: Feature<LineString>, line2: Feature<LineString>): FeatureCollection<Point> {
  return turfLineIntersect(line1, line2);
}

// https://observablehq.com/@danburzo/drawing-svg-rectangles
export function getRectParametersFromSelection(selection: Selection) {
  const { startPosition, endPosition, draggingPosition } = selection;
  const hasBeenDragged = hasCopyPasteBeenDragged(draggingPosition);
  if (!startPosition || (!endPosition && !hasBeenDragged)) return { x: -1, y: -1, width: -1, height: -1 };
  let x, y;
  if (hasBeenDragged) {
    x = draggingPosition.x;
    y = draggingPosition.y;
  } else {
    x = Math.min(startPosition.x, endPosition.x);
    y = Math.min(startPosition.y, endPosition.y);
  }
  const width = Math.abs(endPosition.x - startPosition.x);
  const height = Math.abs(endPosition.y - startPosition.y);
  return { x, y, width, height };
}

export function polygonToLine(
  polygon: Feature<Polygon>
): Feature<MultiLineString | LineString> | FeatureCollection<LineString | MultiLineString> {
  return turfPolygonToLine(polygon);
}

export function getTwoClosestVerticesToLine(points: XYCoord[], line: LineSegment) {
  const lineString = getLineString([
    [line.x1, line.y1],
    [line.x2, line.y2],
  ]);

  const turfPoints = points.map(v => turfPoint([v.x, v.y]));
  const [v0, v1] = turfPoints
    .sort((p0, p1) => {
      const dist0 = turfPointToLineDistance(p0, lineString);
      const dist1 = turfPointToLineDistance(p1, lineString);
      return dist0 - dist1;
    })
    .slice(0, 2)
    .map(p => {
      const [x, y] = p.geometry.coordinates;
      return { x: x, y: y };
    });
  return [v0, v1];
}

export function getPolygonCenterLine(polygon: Feature<Polygon>): Feature<LineString> {
  const shortestEdges = getTwoShortestSidesFromPolygon(polygon);
  const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = shortestEdges.flatMap(({ points }) => verticesMidPoint(points));
  return getLineString([
    [x1, y1],
    [x2, y2],
  ]);
}

export function getVerticesFromPolygon(
  convexHull: Feature<Polygon>,
  mainReferenceLine: LineSegment,
  auxLines: LineSegment[]
): { vertices: XYCoord[]; auxVertices: XYCoord[] } {
  const edges = getTwoShortestSidesFromPolygon(convexHull);
  const allVertices = edges
    .flatMap(({ points }) => {
      const midPoint = verticesMidPoint(points);
      return [midPoint, ...points];
    })
    .map(vertex => ({
      x: roundCoord(vertex.x),
      y: roundCoord(vertex.y),
    }));

  const vertices = getTwoClosestVerticesToLine(allVertices, mainReferenceLine);
  const auxVertices = auxLines.flatMap(line => getTwoClosestVerticesToLine(allVertices, line));
  return { vertices, auxVertices };
}
