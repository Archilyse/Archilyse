import React from 'react';
import { COLORS } from '../../constants';
import { convertPixelsToCMs } from '../../utils/geometry';

const STYLE = {
  stroke: COLORS.SELECTED_ELEMENT,
  strokeWidth: '1px',
};

const STYLE_TEXT = {
  textAnchor: 'middle',
  fontSize: '12px',
  fontFamily: "'Courier New', Courier, monospace",
  pointerEvents: 'none',
  fontWeight: 'bold',

  //http://stackoverflow.com/questions/826782/how-to-disable-text-selection-highlighting-using-css
  WebkitTouchCallout: 'none' /* iOS Safari */,
  WebkitUserSelect: 'none' /* Chrome/Safari/Opera */,
  MozUserSelect: 'none' /* Firefox */,
  MsUserSelect: 'none' /* Internet Explorer/Edge */,
  userSelect: 'none',
} as React.CSSProperties;

type RulerProps = {
  scalingWithOneLine: boolean;
  lineType: string;
  length: number;
  unit: string;
  scale?: number;
  scaleTool: any;
  transform: string;
};

export default function Ruler({
  length,
  unit,
  transform,
  scale: planScale = 1,
  scalingWithOneLine,
  scaleTool,
}: RulerProps) {
  const distanceText = scalingWithOneLine
    ? `${scaleTool.distance || 0} ${unit}`
    : `${convertPixelsToCMs(planScale, length).toFixed(2)} ${unit}`;

  return (
    <g transform={transform}>
      <text x={length / 2} y="-3" transform={`scale(1, -1)`} style={STYLE_TEXT}>
        {distanceText}
      </text>
      <line x1="0" y1="-5" x2="0" y2="5" style={STYLE} />
      <line x1={length} y1="-5" x2={length} y2="5" style={STYLE} />
      <line x1="0" y1="0" x2={length} y2="0" style={STYLE} />
    </g>
  );
}
