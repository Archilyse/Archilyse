import React from 'react';
import { GiEntryDoor } from 'react-icons/gi';
import { MEASURE_STEP_HOLE, OPENING_NAME, OPENING_TYPE } from '../../../constants';
import { getDoorComponentFromStyle } from '../door-common-component';
export default {
  name: OPENING_TYPE.ENTRANCE_DOOR,
  prototype: 'holes',

  info: {
    title: OPENING_NAME.ENTRANCE_DOOR,
    description: OPENING_NAME.ENTRANCE_DOOR,
    toolbarIcon: <GiEntryDoor />,
  },
  help: '(press "R" to rotate/Flip vertical/horizontal)',

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
    flip_horizontal: {
      label: 'flip horizontal',
      type: 'checkbox',
      defaultValue: false,
      values: {
        none: false,
        yes: true,
      },
    },
    flip_vertical: {
      label: 'flip vertical',
      type: 'checkbox',
      defaultValue: true,
      values: {
        right: true,
        left: false,
      },
    },
    heights: {
      label: 'Heights [cm]:',
      type: 'opening_heights',
      defaultValue: { lower_edge: null, upper_edge: null },
    },
  },

  render2D: function EntranceDoor(element, layer, scene) {
    return getDoorComponentFromStyle(element, scene);
  },
};
