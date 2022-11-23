import React from 'react';
import { RiLayoutLeft2Line } from 'react-icons/ri';
import * as GeometryUtils from '../../../utils/geometry';
import { STYLE_SLIDING_DOOR, STYLE_SLIDING_DOOR_SELECTED } from '../style';
import { MEASURE_STEP_HOLE, OPENING_NAME, OPENING_TYPE } from '../../../constants';

export const getSlidingDoorRenderedValues = coordinates => {
  const polygonPoints = GeometryUtils.getUniquePolygonPoints(coordinates)
    .map(([x, y]) => `${x}, ${y}`)
    .join(',');
  return polygonPoints;
};

export default {
  name: OPENING_TYPE.SLIDING_DOOR,
  prototype: 'holes',

  info: {
    title: OPENING_NAME.SLIDING_DOOR,
    toolbarIcon: <RiLayoutLeft2Line />,
    description: 'Wooden door',
  },

  properties: {
    length: {
      label: 'Length',
      type: 'length-measure',
      defaultValue: {
        value: 80,
      },
      step: MEASURE_STEP_HOLE,
    },
    width: {
      label: 'Width',
      type: 'hidden',
      defaultValue: {
        value: 30,
      },
    },
    altitude: {
      label: 'Altitude',
      type: 'hidden',
      defaultValue: {
        value: 0,
      },
    },
    heights: {
      label: 'Heights [cm]:',
      type: 'opening_heights',
      defaultValue: { lower_edge: null, upper_edge: null },
    },
  },

  render2D: function SlidingDoor(element, layer, scene) {
    if (element.coordinates.length > 0) {
      let holeStyle = element.selected ? STYLE_SLIDING_DOOR_SELECTED : STYLE_SLIDING_DOOR;
      const polygonPoints = getSlidingDoorRenderedValues(element.coordinates);
      return (
        <g>
          <polygon points={polygonPoints} style={holeStyle} />
        </g>
      );
    }
    return null;
  },
};
