import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { GiDesk } from 'react-icons/gi';
import { COLORS } from '../../../constants';
const info = {
  title: 'Office Desk',
  description: 'office_desk',
  toolbarIcon: <GiDesk />,
};

export default ElementsFactories.ItemFactory('office_desk', info, { rectStyle: { fill: COLORS.CATALOG.OFFICE_DESK } });
