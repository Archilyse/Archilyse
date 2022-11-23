import React from 'react';
import * as SharedStyle from '../../shared-style';
import { GeometryUtils, PolygonUtils } from '../../utils/export';
import {
  CATALOG_ELEMENT_OPACITY,
  CATALOG_ELEMENT_OPACITY_SELECTED,
  POSSIBLE_WALL_WIDTHS,
  REFERENCE_LINE_POSITION,
  SeparatorsType,
} from '../../constants';

const epsilon = 20;

const ANGLE_PRECISON = 2;

const parseAngle = angle => `${Math.abs(angle).toFixed(ANGLE_PRECISON)}°`;

const getAngle = ({ x1, y1, x2, y2 }) => {
  const angle = GeometryUtils.angleBetweenTwoPoints(x1, y1, x2, y2);
  return GeometryUtils.radToDeg(angle);
};

const getAngleStyle = angle => ({
  textAnchor: 'middle',
  fontSize: '20px',
  stroke: angle.toFixed(ANGLE_PRECISON) % 90 == 0 ? 'green' : 'initial',
});

const getWidthValues = values => {
  const sortedValues = values.slice().sort((a, b) => a - b);
  const result = {};
  for (const width of sortedValues) {
    result[`${width} cm`] = { value: width };
  }
  return result;
};

export const getHelperLinesRenderedValues = (line, layer, scene) => {
  const originalVertices = line.vertices.map(vertexID => layer.vertices[vertexID]);

  const [v0, v1] = originalVertices;
  const vertices = GeometryUtils.orderVertices(originalVertices);
  const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = vertices;

  const length = GeometryUtils.pointsDistance(x1, y1, x2, y2);
  const length5 = length / 5;

  const lineWidthInCM = line.properties.width.value;
  // Here we have to convert the cms defined by the user into pixels for the scene

  const lineWidthInPixels = GeometryUtils.convertCMToPixels(scene.scale, lineWidthInCM);
  const halfLineWidthInPixels = lineWidthInPixels / 2;
  // It is likely that this values are too small depending on the scale
  const halfWidthEps = lineWidthInCM / 2 + epsilon;
  const extraEps = 5;
  const textDistance = halfLineWidthInPixels + epsilon + extraEps;

  const angle = getAngle({ x1, y1, x2, y2 });
  const [[x1p, y1p]] = GeometryUtils.getLinePointsFromReferenceLine(
    { x1, y1, x2, y2 },
    line.properties.referenceLine,
    lineWidthInPixels
  );

  // Use unsorted where the angle should be displayed, to be consistent
  const xForAngle = v0.x < v1.x ? length / 1.25 : length5;

  const textStyle = getAngleStyle(angle);

  return { x1p, y1p, xForAngle, halfWidthEps, textDistance, textStyle, angle };
};

export default function LineFactory(
  name,
  info,
  { help = undefined, widthValues = POSSIBLE_WALL_WIDTHS, defaultWidth = undefined, styleRect = {} } = {}
) {
  const STYLE_LINE = { stroke: SharedStyle.LINE_MESH_COLOR.selected };
  const STYLE_RECT = {
    opacity: CATALOG_ELEMENT_OPACITY,
    strokeWidth: 0,
    stroke: styleRect?.fill || SharedStyle.LINE_MESH_COLOR.unselected,
    fill: 'url(#diagonalFill)',
    ...styleRect,
  };
  const STYLE_RECT_SELECTED = {
    ...STYLE_RECT,
    opacity: CATALOG_ELEMENT_OPACITY_SELECTED,
    stroke: SharedStyle.LINE_MESH_COLOR.selected,
    strokeWidth: 1,
  };

  const renderElementPolygon = (line, style) => {
    const coordinates = line.coordinates; // line.coordinates: number[][][]
    const polygonPoints = PolygonUtils.coordsToSVGPoints(coordinates);
    return <polygon role="presentation" points={polygonPoints} style={style} />;
  };

  const LineElement = {
    name,
    prototype: 'lines',
    info,
    help:
      name === SeparatorsType.AREA_SPLITTER
        ? ''
        : '(press "+/-" to change width) \n (press "f" to change reference line)',
    properties: {
      referenceLine: {
        label: 'Reference Line',
        type: name === SeparatorsType.AREA_SPLITTER ? 'hidden' : 'enum',
        defaultValue: REFERENCE_LINE_POSITION.OUTSIDE_FACE,
        values: {
          [REFERENCE_LINE_POSITION.CENTER]: 'Center',
          [REFERENCE_LINE_POSITION.OUTSIDE_FACE]: 'Outside face',
          [REFERENCE_LINE_POSITION.INSIDE_FACE]: 'Inside face',
        },
      },
      height: {
        label: 'height',
        type: 'hidden',
        defaultValue: {
          value: 300,
        },
      },
      width: {
        label: 'width',
        type: 'enum-length-measure',
        defaultValue: {
          value: widthValues.find(width => width === defaultWidth) || widthValues[0],
        },
        values: getWidthValues(widthValues),
      },
    },

    render2D: function (line, layer, scene) {
      const { x1p, y1p, xForAngle, halfWidthEps, textDistance, textStyle, angle } = getHelperLinesRenderedValues(
        line,
        layer,
        scene
      );
      const lineStyles = line.selected ? STYLE_RECT_SELECTED : STYLE_RECT;

      return (
        <>
          {renderElementPolygon(line, lineStyles)}
          {line.selected && (
            <g transform={`translate(${x1p}, ${y1p}) rotate(${angle}, 0, 0)`}>
              <line x1={xForAngle} y1={-halfWidthEps} x2={xForAngle} y2={halfWidthEps} style={STYLE_LINE} />
              {angle != null && (
                <text
                  data-testid={`viewer-line-${line.id}-angle`}
                  x={xForAngle}
                  y={textDistance}
                  style={textStyle}
                  transform={`scale(1, -1)`}
                >
                  {parseAngle(angle)}
                </text>
              )}
            </g>
          )}
        </>
      );
    },
  };

  return LineElement;
}
