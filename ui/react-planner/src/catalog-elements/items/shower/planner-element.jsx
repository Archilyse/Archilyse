import React from 'react';
import { FaShower } from 'react-icons/fa';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';

const info = {
  title: 'Shower',
  description: 'shower',
  toolbarIcon: <FaShower />,
};

export default ElementsFactories.ItemFactory('shower', info, { rectStyle: { fill: COLORS.CATALOG.SHOWER } });
