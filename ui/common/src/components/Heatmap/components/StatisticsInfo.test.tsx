import React from 'react';
import { render, screen } from '@testing-library/react';
import StatisticsInfo, { HeatmapStatistics } from './StatisticsInfo';

// mock it because jest couldn't parse `north` image, although we set module mapper in config
jest.mock('./NorthArrow', () => {
  return () => null;
});

it.each([
  ['building', [0, 5.5], ['0.0', '5.5'], 'sr'],
  ['noise_TRAIN_DAY', [0, 60], ['0', '> 60'], 'dBA'],
  ['sun-2018-03-21 08:00:00+01:00', [0, 3], ['0', '3000'], 'lx'],
  ['connectivity_BALCONY_distance', [0, 14.534], ['0.00', '14.53'], ''],
])('renders statistics of %s dimention correctly', (dimension, [min, max], legends, unit) => {
  const statistics: HeatmapStatistics = { min, max, average: 0, std: 0 };

  render(<StatisticsInfo simulationName={dimension} statistics={statistics} size="medium" />);

  if (unit) {
    expect(screen.getByText(`Values = ${unit}`)).toBeInTheDocument();
  }

  legends.forEach(legend => {
    expect(screen.getByText(legend)).toBeInTheDocument();
  });
});
