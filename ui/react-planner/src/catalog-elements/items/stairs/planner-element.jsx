import React from 'react';
import { GiStairs } from 'react-icons/gi';
import { ITEM_DIRECTION, COLORS } from '../../../constants';
import ElementsFactories from '../../../catalog/factories/export';

const info = {
  title: 'Stairs',
  toolbarIcon: <GiStairs />,
  description: 'Simple stairs',
};

const DEFAULT_LENGTH = 150;
const DEFAULT_WIDTH = 90;

const additionalProperties = {
  altitude: {
    label: 'altitude',
    type: 'hidden',
    defaultValue: {
      value: 0,
      unit: 'cm',
    },
  },
  direction: {
    label: 'direction',
    type: 'enum',
    defaultValue: ITEM_DIRECTION.UP,
    values: { [ITEM_DIRECTION.UP]: 'Up', [ITEM_DIRECTION.DOWN]: 'Down' },
  },
};

export default ElementsFactories.ItemFactory('stairs', info, {
  rectStyle: { fill: COLORS.CATALOG.STAIRS },
  defaultWidth: DEFAULT_WIDTH,
  defaultLength: DEFAULT_LENGTH,
  additionalProperties,
});
