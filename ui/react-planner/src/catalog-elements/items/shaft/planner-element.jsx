import React from 'react';
import { BsXCircle } from 'react-icons/bs';

import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const DEFAULT_SHAFT_WIDTH = 10;
const DEFAULT_SHAFT_LENGTH = 10;

const info = {
  title: 'Shaft',
  description: 'shaft',
  toolbarIcon: <BsXCircle />,
};

export default ElementsFactories.ItemFactory('shaft', info, {
  rectStyle: { fill: COLORS.CATALOG.SHAFT },
  defaultWidth: DEFAULT_SHAFT_WIDTH,
  defaultLength: DEFAULT_SHAFT_LENGTH,
});
