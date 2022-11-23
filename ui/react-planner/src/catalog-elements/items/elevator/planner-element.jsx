import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { GiElevator } from 'react-icons/gi';
import { COLORS } from '../../../constants';
const info = {
  title: 'Elevator',
  description: 'elevator',
  toolbarIcon: <GiElevator />,
};
export default ElementsFactories.ItemFactory('elevator', info, {
  rectStyle: { fill: COLORS.CATALOG.ELEVATOR },
  defaultWidth: 100,
  defaultLength: 100,
});
