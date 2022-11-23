import React from 'react';
import { BsSquare } from 'react-icons/bs';
import * as GeometryUtils from '../../../utils/geometry';
import { STYLE_WINDOW_BASE, STYLE_WINDOW_SELECTED, PADDING } from '../style';
import { MEASURE_STEP_HOLE, OPENING_NAME, OPENING_TYPE } from '../../../constants';

export default {
  name: OPENING_TYPE.WINDOW,
  prototype: 'holes',

  info: {
    title: OPENING_NAME.WINDOW,
    description: OPENING_NAME.WINDOW,
    toolbarIcon: <BsSquare />,
  },

  properties: {
    length: {
      label: 'Length',
      type: 'length-measure',
      defaultValue: {
        value: 90,
      },
      step: MEASURE_STEP_HOLE,
    },
    width: {
      label: 'Width',
      type: 'hidden',
      defaultValue: {
        value: 10,
      },
    },

    altitude: {
      label: 'Altitude',
      type: 'hidden',
      defaultValue: {
        value: 90,
      },
    },
    heights: {
      label: 'Heights [cm]:',
      type: 'opening_heights',
      defaultValue: { lower_edge: null, upper_edge: null },
    },
  },
  getWindowRenderedValues: (element, layer) => {
    const parentLine = layer.lines[element.line];
    const coordinates = element.coordinates;

    const [firstVertexId, secondVertexId] = parentLine.vertices;
    const vertex0 = layer.vertices[firstVertexId];
    const vertex1 = layer.vertices[secondVertexId];
    const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = GeometryUtils.orderVertices([vertex0, vertex1]);
    const angle = GeometryUtils.angleBetweenTwoPointsAndOrigin(x1, y1, x2, y2);
    const coordinatesNoClosingVertex = GeometryUtils.getUniquePolygonPoints(coordinates);
    const verticesIndexed = coordinatesNoClosingVertex.map(([x, y]) => {
      return { x: x, y: y };
    });
    const { x: cx, y: cy } = GeometryUtils.verticesMidPoint(verticesIndexed);
    const polygonPoints = coordinatesNoClosingVertex.map(([x, y]) => `${x}, ${y}`).join(',');
    return {
      polygonPoints,
      cx,
      cy,
      angle,
    };
  },
  render2D: function Window(element, layer, scene) {
    if (element.coordinates.length > 0) {
      const style = element.selected ? STYLE_WINDOW_SELECTED : STYLE_WINDOW_BASE;
      const { polygonPoints, cx, cy, angle } = this.getWindowRenderedValues(element, layer);

      return (
        <g data-testid="hole-window">
          <polygon data-testid="hole-window-polygon" points={polygonPoints} style={style} />
          <line
            transform={`translate(${cx}, ${cy}) rotate(${angle}, 0, 0)`}
            x1={0}
            y1={-10}
            x2={0}
            y2={10}
            style={{ ...style, strokeWidth: PADDING / 2 }}
          />
        </g>
      );
    }
    return null;
  },
};
