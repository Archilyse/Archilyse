import React from 'react';
import { FaToilet } from 'react-icons/fa';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const info = {
  title: 'Toilet',
  description: 'toilet',
  toolbarIcon: <FaToilet />,
};

export default ElementsFactories.ItemFactory('toilet', info, { rectStyle: { fill: COLORS.CATALOG.TOILET } });
