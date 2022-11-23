import React from 'react';
import * as GeometryUtils from '../../utils/geometry';

import { OPENING_TYPE } from '../../constants';
import { DOOR_STYLE, ENTRANCE_DOOR_STYLE } from './style';

import { getArcSvgPathFromSweepingPoints } from './utils';

export const getDoorRenderedValues = (element, scene) => {
  const holeLength = GeometryUtils.getElementLengthInPixels(element, scene.scale);
  const anglePoint = element.door_sweeping_points?.angle_point;
  const openedPoint = element.door_sweeping_points?.opened_point;
  const closedPoint = element.door_sweeping_points?.closed_point;
  const [ax, ay] = anglePoint;
  const [ox, oy] = openedPoint;
  const arcPath = getArcSvgPathFromSweepingPoints(
    { angle_point: anglePoint, opened_point: openedPoint, closed_point: closedPoint },
    holeLength
  );
  const clippingPath = arcPath + ` L${anglePoint} L${closedPoint} Z`;

  const coordinates = element.coordinates;
  const polygonPoints = GeometryUtils.getUniquePolygonPoints(coordinates)
    .map(([x, y]) => `${x}, ${y}`)
    .join(',');

  return { clippingPath, polygonPoints, ax, ay, ox, oy, arcPath };
};

export const getDoorComponentFromStyle = (element, scene) => {
  const doorStyleFunction = element.type == OPENING_TYPE.ENTRANCE_DOOR ? ENTRANCE_DOOR_STYLE : DOOR_STYLE;
  const applicableStyle = doorStyleFunction(element.selected);
  if (element.coordinates.length > 0 && element.door_sweeping_points) {
    const { clippingPath, polygonPoints, ax, ay, ox, oy, arcPath } = getDoorRenderedValues(element, scene);
    return (
      <g>
        <defs>
          <clipPath id={`clip-path-${element.id}`}>
            <path data-testid={`door-sweeping-points-${element.id}`} d={clippingPath} />
          </clipPath>
        </defs>
        <path d={arcPath} style={applicableStyle.arc} clipPath={`url(#clip-path-${element.id})`} />
        <line x1={ax} y1={ay} x2={ox} y2={oy} style={applicableStyle.base} clipPath={`url(#clip-path-${element.id})`} />
        <polygon points={polygonPoints} style={applicableStyle.polygon} />
      </g>
    );
  }
  return null;
};
