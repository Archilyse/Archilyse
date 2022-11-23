import React from 'react';
import { FaRulerHorizontal } from 'react-icons/fa';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS, DEFAULT_WALL_WIDTH, SeparatorsType } from '../../../constants';

const info = {
  title: 'Scale Tool',
  description: 'Scale the plan',
  toolbarIcon: <FaRulerHorizontal />,
  visibility: {
    catalog: false,
    layerElementsVisible: true,
  },
};

export default ElementsFactories.LineFactory(SeparatorsType.SCALE_TOOL, info, {
  defaultWidth: DEFAULT_WALL_WIDTH,
  styleRect: { fill: COLORS.CATALOG.SCALE_TOOL, opacity: 1 },
});
