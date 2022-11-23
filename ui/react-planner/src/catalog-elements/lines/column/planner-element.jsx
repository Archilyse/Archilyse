import React from 'react';
import { GiIonicColumn } from 'react-icons/gi';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS, SeparatorsType } from '../../../constants';
const info = {
  title: 'Column',
  description: 'column',
  toolbarIcon: <GiIonicColumn />,
};

export default ElementsFactories.LineFactory(SeparatorsType.COLUMN, info, {
  styleRect: { fill: COLORS.CATALOG.COLUMN, stroke: COLORS.CATALOG.COLUMN },
  defaultWidth: 40,
});
