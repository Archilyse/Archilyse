import React from 'react';
import ElementsFactories from '../../../catalog/factories/export';
import { BsLayoutSplit } from 'react-icons/bs';
import { COLORS, SeparatorsType, DEFAULT_AREA_SPLITTER_WIDTH } from '../../../constants';
const info = {
  title: 'Area Splitter',
  description: 'Split one area into two',
  toolbarIcon: <BsLayoutSplit />,
  visibility: {
    catalog: true,
    layerElementsVisible: true,
  },
};

export default ElementsFactories.LineFactory(SeparatorsType.AREA_SPLITTER, info, {
  widthValues: [DEFAULT_AREA_SPLITTER_WIDTH],
  styleRect: { fill: COLORS.CATALOG.AREA_SPLITTER, strokeWidth: 10 },
});
