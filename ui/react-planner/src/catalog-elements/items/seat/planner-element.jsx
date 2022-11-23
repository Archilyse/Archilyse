import React from 'react';
import { BiChair } from 'react-icons/bi';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const DEFAULT_WIDTH = 55;
const DEFAULT_LENGTH = 50;

const info = {
  title: 'Seat',
  toolbarIcon: <BiChair />,
  description: 'seat',
};

const additionalProperties = {
  altitude: {
    label: 'altitude',
    type: 'hidden',
    defaultValue: {
      value: 0,
      unit: 'cm',
    },
  },
};

export default ElementsFactories.ItemFactory('seat', info, {
  rectStyle: { fill: COLORS.CATALOG.SEAT },
  additionalProperties,
  defaultWidth: DEFAULT_WIDTH,
  defaultLength: DEFAULT_LENGTH,
});
