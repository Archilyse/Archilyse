import React from 'react';
import { COLORS } from '../../constants';
import './copyPasteSelection.css';

const STYLE_CIRCLE = {
  fill: COLORS.SELECTED_ELEMENT,
  stroke: COLORS.SELECTED_ELEMENT,
  cursor: 'ew-resize',
};

const STYLE_CIRCLE2 = {
  fill: 'none',
  stroke: COLORS.SELECTED_ELEMENT,
  cursor: 'ew-resize',
};

const ARROW_STYLE = {
  stroke: COLORS.SELECTED_ELEMENT,
  strokeWidth: '2px',
  fill: COLORS.SELECTED_ELEMENT,
};

const ARROW_X_POS = 40;
const ARROW_Y_POS = 50;

const ARROW_HEIGHT = 60;
const ARROW_WIDTH = 45;
const ROTATION_ANCHOR_RADIUS = 30;

export const RotationCircle = ({ width, height, rotationCircleRadius }) => (
  <g data-testid="copy-paste-rotation-anchor">
    <g
      data-part="rotation-orientation-arrow"
      transform={`translate(${width}, ${height + rotationCircleRadius - ARROW_Y_POS})`}
    >
      <line key="2" x1={0} x2={0} y1={ARROW_Y_POS} y2={ARROW_Y_POS + ARROW_HEIGHT} style={ARROW_STYLE} />
      <line
        key="3"
        x1={0.25 * ARROW_X_POS}
        x2={0}
        y1={ARROW_Y_POS + ARROW_WIDTH}
        y2={ARROW_Y_POS + ARROW_HEIGHT}
        style={ARROW_STYLE}
      />
      <line
        key="4"
        x1={0}
        x2={-0.25 * ARROW_X_POS}
        y1={ARROW_Y_POS + ARROW_HEIGHT}
        y2={ARROW_Y_POS + ARROW_WIDTH}
        style={ARROW_STYLE}
      />
    </g>
    <circle
      data-part="rotation-anchor"
      cx={width}
      cy={height + rotationCircleRadius}
      r={ROTATION_ANCHOR_RADIUS}
      style={STYLE_CIRCLE}
    />
    <circle data-part="rotation-anchor" cx={width} cy={height} r={rotationCircleRadius} style={STYLE_CIRCLE2} />
  </g>
);

export default RotationCircle;
