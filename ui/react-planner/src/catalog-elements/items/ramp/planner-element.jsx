import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { RiArrowRightUpLine } from 'react-icons/ri';
import { COLORS } from '../../../constants';
const info = {
  title: 'Ramp',
  description: 'ramp',
  toolbarIcon: <RiArrowRightUpLine />,
};

export default ElementsFactories.ItemFactory('ramp', info, { rectStyle: { fill: COLORS.CATALOG.RAMP } });
