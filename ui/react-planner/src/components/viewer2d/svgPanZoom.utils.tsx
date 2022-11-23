import * as PolygonUtils from '../../utils/polygon-utils';
import { getHelperLinesRenderedValues } from '../../catalog/factories/line-factory';
import windowPlannerElement from '../../catalog-elements/holes/window/planner-element';
import { getDoorRenderedValues } from '../../catalog-elements/holes/door-common-component';
import { getSlidingDoorRenderedValues } from '../../catalog-elements/holes/sliding-door/planner-element';
import { OPENING_TYPE } from '../../constants';
import { getCopyPasteSelectionValues } from './copyPasteSelection';

interface setSelectionTransformParams {
  copyPasteElem: Element;
  updatedState: any;
  setRectangleDimensions: boolean;
  selectionType?: 'copyPaste' | 'rectangleTool';
}

export const setCopyPasteSelectionTransform = ({
  copyPasteElem,
  updatedState,
  setRectangleDimensions = false,
  selectionType = 'copyPaste',
}: setSelectionTransformParams) => {
  const { startPosition, endPosition, draggingPosition, rotation = 0 } = updatedState[selectionType].selection;

  const { x, y, width, height, halfWidth, halfHeight } = getCopyPasteSelectionValues({
    startPosition,
    endPosition,
    draggingPosition,
  });

  copyPasteElem.setAttribute('transform', `translate(${x}, ${y}) rotate(${rotation}, ${halfWidth}, ${halfHeight})`);

  if (setRectangleDimensions) {
    const copyPasteRect = copyPasteElem?.firstChild as HTMLElement;
    copyPasteRect.setAttribute('width', String(width));
    copyPasteRect.setAttribute('height', String(height));
  }
};

export const setSelectedVerticesTransform = ({ updatedState, selectedLayer }) => {
  const allVertices = Object.values(updatedState.scene.layers[selectedLayer].vertices) as any;
  const selectedVertices = allVertices.filter(v => v.selected);
  selectedVertices.map(selectedVertex => {
    const { id } = selectedVertex;
    const vertexElem = document.querySelector(`g[data-id="${id}"]`);
    vertexElem.setAttribute('transform', `translate(${selectedVertex.x}, ${selectedVertex.y})`);
    vertexElem.setAttribute('data-coords', JSON.stringify({ x: selectedVertex.x, y: selectedVertex.y }));
  });
};

export const setSelectedLinesTransform = ({ updatedState, selectedLayer }) => {
  const updatedLines = updatedState.scene.layers[selectedLayer].lines;
  const allLines = Object.values(updatedLines) as any;
  const selectedLines = allLines.filter(v => v.selected);
  selectedLines.forEach(selectedLine => {
    const { id } = selectedLine;
    const updatedLine = updatedLines[id];
    const coordinates = updatedLine.coordinates;
    const polygonPoints = PolygonUtils.coordsToSVGPoints(coordinates);

    const polygon = document.querySelector(`g[data-id="${id}"] polygon`);

    polygon.setAttribute('points', polygonPoints);

    // Set helper lines
    const layer = updatedState.scene.layers[selectedLayer];
    const scene = updatedState.scene;
    const { x1p, y1p, xForAngle, halfWidthEps, textDistance, textStyle, angle } = getHelperLinesRenderedValues(
      selectedLine,
      layer,
      scene
    );

    const nextSibling = polygon.nextSibling;
    const nextSiblingLine = (nextSibling as Element).querySelector('line');
    const nextSiblingText = (nextSibling as Element).querySelector('text');
    (nextSibling as Element).setAttribute('transform', `translate(${x1p}, ${y1p}) rotate(${angle}, 0, 0)`);
    nextSiblingLine.setAttribute('x1', xForAngle as string);
    nextSiblingLine.setAttribute('y1', String(-halfWidthEps));
    nextSiblingLine.setAttribute('x2', xForAngle as string);
    nextSiblingLine.setAttribute('y', String(-halfWidthEps));

    nextSiblingText.setAttribute('x', xForAngle as string);
    nextSiblingText.setAttribute('y', textDistance as string);
    nextSiblingText.setAttribute('style', textStyle);

    const rulerElem = polygon.parentNode.querySelector('.ruler');
    rulerElem.setAttribute('transform', `translate(${x1p}, ${y1p}) rotate(${angle}, 0, 0)`);
  });
};

export const setSelectedItemsTransform = ({ updatedState, selectedLayer }) => {
  const allItems = Object.values(updatedState.scene.layers[selectedLayer].items) as any;
  const selectedItems = allItems.filter(v => v.selected);
  selectedItems.forEach(selectedItem => {
    const { id, x, y, rotation } = selectedItem;
    const itemElem = document.querySelector(`g[data-id="${id}"]`);
    itemElem.setAttribute('transform', `translate(${x},${y}) rotate(${rotation})`);
    itemElem.setAttribute('data-coords', JSON.stringify({ x, y, rotation }));
  });
};

export const setSelectedHolesCoordinates = ({ updatedState, selectedLayer }) => {
  const scene = updatedState.scene;
  const allHoles = Object.values(updatedState.scene.layers[selectedLayer].holes) as any;
  const selectedHoles = allHoles.filter(v => v.selected);
  selectedHoles.forEach(selectedHole => {
    const { id, coordinates, type } = selectedHole;
    const holeElem = document.querySelector(`g[data-id="${id}"]`);
    const polygonElem = holeElem.querySelector('g polygon');
    const lineElem = holeElem.querySelector('g line');
    polygonElem.setAttribute('data-coords', JSON.stringify(coordinates));
    if (type === OPENING_TYPE.DOOR || type === OPENING_TYPE.ENTRANCE_DOOR) {
      const { clippingPath, polygonPoints, ax, ay, ox, oy, arcPath } = getDoorRenderedValues(selectedHole, scene);

      const clipPathElem = holeElem.querySelector('g defs clipPath path');
      const pathElem = holeElem.querySelector('g > path');
      polygonElem.setAttribute('points', polygonPoints);
      lineElem.setAttribute('x1', ax);
      lineElem.setAttribute('y1', ay);
      lineElem.setAttribute('x2', ox);
      lineElem.setAttribute('y2', oy);
      pathElem.setAttribute('d', arcPath);
      clipPathElem.setAttribute('d', clippingPath);
    } else if (type === OPENING_TYPE.WINDOW) {
      const layer = updatedState.scene.layers[selectedLayer];
      const { polygonPoints, cx, cy, angle } = windowPlannerElement.getWindowRenderedValues(selectedHole, layer);

      polygonElem.setAttribute('points', polygonPoints);
      lineElem.setAttribute('transform', `translate(${cx}, ${cy}) rotate(${angle}, 0, 0)`);
    } else if (type === OPENING_TYPE.SLIDING_DOOR) {
      const elementCoordinates = selectedHole.coordinates;
      const polygonPoints = getSlidingDoorRenderedValues(elementCoordinates);
      polygonElem.setAttribute('points', polygonPoints);
    }
  });
};

export const updateSelectedAnnotations = ({ updatedState }) => {
  const selectedLayer = updatedState.scene.selectedLayer;

  // Update vertices coordinates
  setSelectedVerticesTransform({ updatedState, selectedLayer });

  // Update lines and helper lines coordinates
  setSelectedLinesTransform({ updatedState, selectedLayer });

  // Update Items transform coordinates
  setSelectedItemsTransform({ updatedState, selectedLayer });

  // Update Holes transform coordinates
  setSelectedHolesCoordinates({ updatedState, selectedLayer });
};
