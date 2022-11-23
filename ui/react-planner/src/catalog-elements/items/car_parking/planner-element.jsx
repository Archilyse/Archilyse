import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { MdLocalParking } from 'react-icons/md';
import { COLORS } from '../../../constants';
const info = {
  title: 'Car Parking',
  description: 'Car Parking',
  toolbarIcon: <MdLocalParking />,
};
export default ElementsFactories.ItemFactory('car_parking', info, {
  rectStyle: { fill: COLORS.CATALOG.CAR_PARKING },
});
