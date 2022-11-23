import React from 'react';
import { BiBath } from 'react-icons/bi';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const info = {
  title: 'Bathtub',
  description: 'Bathtub',
  toolbarIcon: <BiBath />,
};

export default ElementsFactories.ItemFactory('bathtub', info, {
  rectStyle: { fill: COLORS.CATALOG.BATHTUB },
});
