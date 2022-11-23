import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { BiCabinet } from 'react-icons/bi';
import { COLORS } from '../../../constants';
const info = {
  title: 'Built In Furniture',
  description: 'Built In Furniture',
  toolbarIcon: <BiCabinet />,
};

export default ElementsFactories.ItemFactory('built_in_furniture', info, {
  rectStyle: { fill: COLORS.CATALOG.RAMP },
  defaultWidth: 60,
  defaultLength: 60,
});
