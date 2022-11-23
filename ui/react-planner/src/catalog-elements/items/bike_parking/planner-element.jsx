import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { MdDirectionsBike } from 'react-icons/md';
import { COLORS } from '../../../constants';
const info = {
  title: 'Bike Parking',
  description: 'Bike Parking',
  toolbarIcon: <MdDirectionsBike />,
};

export default ElementsFactories.ItemFactory('bike_parking', info, {
  rectStyle: { fill: COLORS.CATALOG.BIKE_PARKING },
});
