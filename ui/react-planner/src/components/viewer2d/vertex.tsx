import React from 'react';
import * as SharedStyle from '../../shared-style';
import {
  CIRCLE_RADIUS,
  CIRCLE_RADIUS_REFERENCE,
  COLORS,
  VERTEX_DEFAULT_OPACITY,
  VERTEX_SCALING_OPACITY,
} from '../../constants';
import { Vertex as VertexType } from '../../types';

type VertexProps = {
  layer: any;
  isScaling: boolean;
  vertex: VertexType;
};
export default function Vertex({ vertex, layer, isScaling }: VertexProps) {
  const { x, y } = vertex;

  // is main vertex
  const formsReferenceLine = vertex.lines.some(lineId => {
    const line = layer.lines[lineId];
    return line && line.selected && line.vertices.includes(vertex.id);
  });

  const style = {
    fill: COLORS.SELECTED_ELEMENT,
    fillOpacity: isScaling ? VERTEX_SCALING_OPACITY : VERTEX_DEFAULT_OPACITY,
    stroke: formsReferenceLine ? SharedStyle.COLORS.dark_blue : SharedStyle.COLORS.white,
    cursor: formsReferenceLine ? 'move' : 'default',
  };

  return (
    <g
      transform={`translate(${x}, ${y})`}
      data-testid={`vertex-${vertex.id}`}
      data-element-root
      data-prototype={vertex.prototype}
      data-id={vertex.id}
      data-selected={vertex.selected}
      data-layer={layer.id}
    >
      <circle cx="0" cy="0" r={formsReferenceLine ? CIRCLE_RADIUS_REFERENCE : CIRCLE_RADIUS} style={style} />
    </g>
  );
}
