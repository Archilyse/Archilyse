import React from 'react';
import { FaGripLines } from 'react-icons/fa';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS, SeparatorsType } from '../../../constants';
const info = {
  title: 'Railing',
  description: 'Railing',
  toolbarIcon: <FaGripLines />,
  visibility: {
    catalog: true,
    layerElementsVisible: true,
  },
};

export default ElementsFactories.LineFactory(SeparatorsType.RAILING, info, {
  styleRect: { fill: COLORS.CATALOG.RAILINGS, stroke: COLORS.CATALOG.RAILINGS },
});
