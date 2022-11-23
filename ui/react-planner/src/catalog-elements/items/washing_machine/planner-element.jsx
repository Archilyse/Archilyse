import React from 'react';
import { CgSmartHomeWashMachine } from 'react-icons/cg';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const info = {
  title: 'Washing Machine',
  description: 'Washing Machine',
  toolbarIcon: <CgSmartHomeWashMachine />,
};
export default ElementsFactories.ItemFactory('washing_machine', info, {
  rectStyle: { fill: COLORS.CATALOG.WASHING_MACHINE },
  defaultWidth: 60,
  defaultLength: 60,
});
