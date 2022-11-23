import React from 'react';
import { GiBrickWall } from 'react-icons/gi';
import { COLORS, DEFAULT_WALL_WIDTH, SeparatorsType } from '../../../constants';
import ElementsFactories from '../../../catalog/factories/export';

const info = {
  title: 'Wall',
  description: 'Wall with bricks or painted',
  toolbarIcon: <GiBrickWall />,
  visibility: {
    catalog: true,
    layerElementsVisible: true,
  },
};

export default ElementsFactories.LineFactory(SeparatorsType.WALL, info, {
  defaultWidth: DEFAULT_WALL_WIDTH,
  styleRect: {
    fill: COLORS.CATALOG.WALL,
  },
});
