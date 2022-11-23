import React from 'react';
import cn from 'classnames';
import { HeatmapProps } from '..';
import north from '../../../../assets/images/north.png';

const NORTH_ARROW_WIDTH_BY_SIZE: Record<HeatmapProps['infoSize'], number> = {
  medium: 90,
  small: 60,
};

const NorthArrow = ({ angle = 0, size }) => {
  const width = NORTH_ARROW_WIDTH_BY_SIZE[size];

  return (
    <div className={cn('northArrow', size)}>
      <img style={{ transform: `rotate(${angle}deg)`, width }} src={north} alt="north indicator" />
    </div>
  );
};

export default NorthArrow;
