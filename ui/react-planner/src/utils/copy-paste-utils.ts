import * as GeometryUtils from '../utils/geometry';
import { Line } from '../class/export';
import { StorageCopyPaste, Vertex as VertexType } from '../types';
import { getSelectedLayer } from '../utils/state-utils';
import { SeparatorsType } from '../constants';

export const getSelectionCenter = selection => {
  const { width, height, x, y } = GeometryUtils.getRectParametersFromSelection(selection);
  return {
    x: x + width / 2,
    y: y + height / 2,
  };
};

export const getSelectionPolygonPoints = (startPosition, endPosition) => {
  const { x, y, width, height } = GeometryUtils.getRectParametersFromSelection({
    startPosition,
    endPosition,
    draggingPosition: { x: -1, y: -1 },
  });

  //Following: https://gist.github.com/marynaaleksandrova/1a653fa29b8a605d3b7879e8d16f1afc
  const newX = x + width;
  const newY = y + height;

  const polygonPoints = [
    [x, y],
    [newX, y],
    [newX, newY],
    [x, newY],
    [x, y], // Following GeoJSON standard, same as first one
  ];
  return polygonPoints;
};

export const detectItemsUnderSelection = (state, layerID, startPosition, endPosition) => {
  const polygonPoints = getSelectionPolygonPoints(startPosition, endPosition);
  const selectionPolygon = GeometryUtils.createPolygon([polygonPoints]);

  const layer = state.scene.layers[layerID];

  // @TODO: Memoize the item points/polygon creation
  const itemsThatIntersects = Object.values(layer.items).filter((item: any) => {
    const itemWidthInPx = GeometryUtils.getElementWidthInPixels(item, state.scene.scale);
    const itemLengthInPx = GeometryUtils.getElementLengthInPixels(item, state.scene.scale);

    const itemPolygon = GeometryUtils.getItemPolygon(item.x, item.y, item.rotation, itemWidthInPx, itemLengthInPx);
    return GeometryUtils.booleanIntersects(itemPolygon, selectionPolygon);
  });
  return itemsThatIntersects;
};

export const detectLinesUnderSelection = (state, layerID, startPosition, endPosition) => {
  const polygonPoints = getSelectionPolygonPoints(startPosition, endPosition);
  const selectionPolygon = GeometryUtils.createPolygon([polygonPoints]);
  const layer = state.scene.layers[layerID];

  // @TODO: Memoize the line points/polygon creation
  const linesThatIntersect = Object.values(layer.lines).filter(line => {
    const linePolygon = Line.getPolygon(line);
    // some lines are drawn differently because of postprocessing and Line.getPolygon can return null
    // @TODO investigate why Line.getPolygon returns null sometimes
    if (linePolygon) {
      return GeometryUtils.booleanIntersects(linePolygon, selectionPolygon);
    } else {
      return false;
    }
  });

  return linesThatIntersect;
};

export const detectElementsUnderSelection = (state, layerID, selection) => {
  const startPosition = selection.startPosition;
  const endPosition = selection.endPosition;

  const lines = detectLinesUnderSelection(state, layerID, startPosition, endPosition); // Detecting lines we also have the holes on it
  const items = detectItemsUnderSelection(state, layerID, startPosition, endPosition);
  return { lines, items };
};

export const getVerticesToTransform = (state): { [id: string]: VertexType } => {
  const copyPastedLines = state.copyPaste.selection.lines;
  const layer = getSelectedLayer(state.scene);
  const layerVertices = layer.vertices;

  const verticesToTransform = copyPastedLines.reduce((accum, lineID) => {
    const line = layer.lines[lineID];

    line.vertices.concat(line.auxVertices).forEach(vertexID => {
      const vertex = layerVertices[vertexID];
      accum[vertex.id] = vertex;
    });
    return accum;
  }, {});
  return verticesToTransform;
};

export const getCopiedElements = (state): StorageCopyPaste['elements'] => {
  const layer = getSelectedLayer(state.scene);
  const copyPastedLineIDs = state.copyPaste.selection.lines || [];
  const copyPastedItemIDs = state.copyPaste.selection.items || [];
  const copyPastedHoleIDs = state.copyPaste.selection.holes || [];

  return {
    vertices: Object.values(getVerticesToTransform(state)),
    lines: copyPastedLineIDs.map(lineID => layer.lines[lineID]),
    items: copyPastedItemIDs.map(itemID => layer.items[itemID]),
    holes: copyPastedHoleIDs.map(holeID => layer.holes[holeID]),
  };
};

export const isFromAreaSplitter = (state, layerID, vertex) => {
  return vertex.lines.some(lineID => {
    const line = state.scene.layers[layerID].lines[lineID];
    return line.type === SeparatorsType.AREA_SPLITTER;
  });
};

export const findRepeatedVerticesForVertex = (state, layerID, copyPastedVertices, vertex) => {
  if (isFromAreaSplitter(state, layerID, vertex)) return [];

  return copyPastedVertices.filter(v => {
    const samePoint = v.id !== vertex.id && GeometryUtils.samePoints(vertex, v); // @TODO: Ensure both are not in the same line
    const sameLines = vertex.lines.every(lineID => v.lines.includes(lineID));
    return samePoint && !sameLines && !isFromAreaSplitter(state, layerID, v);
  });
};
