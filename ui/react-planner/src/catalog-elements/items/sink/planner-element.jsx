import React from 'react';
import { GiLava } from 'react-icons/gi';
import ElementsFactories from '../../../catalog/factories/export';
import { COLORS } from '../../../constants';
const DEFAULT_LENGTH = 60;
const DEFAULT_WIDTH = 50;

const info = {
  title: 'Sink',
  toolbarIcon: <GiLava />,
  description: 'sink',
};

export default ElementsFactories.ItemFactory('sink', info, {
  rectStyle: { fill: COLORS.CATALOG.SINK },
  defaultWidth: DEFAULT_WIDTH,
  defaultLength: DEFAULT_LENGTH,
});
