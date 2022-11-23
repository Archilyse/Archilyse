import React from 'react';
import { MdKitchen } from 'react-icons/md';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const DEFAULT_WIDTH = 60;
const DEFAULT_LENGTH = 60;

const info = {
  title: 'Kitchen',
  description: 'kitchen',
  toolbarIcon: <MdKitchen />, // @TODO: Change icon
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

export default ElementsFactories.ItemFactory('kitchen', info, {
  rectStyle: { fill: COLORS.CATALOG.KITCHEN },
  additionalProperties,
  defaultWidth: DEFAULT_WIDTH,
  defaultLength: DEFAULT_LENGTH,
});
