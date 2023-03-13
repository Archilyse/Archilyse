import HeatmapStatisticsUtils, { DEFAULT_SPHERICAL_MAX, SPHERICAL_MAX_MIN } from './HeatmapStatisticsUtils';

it.each([
  [undefined, ''],
  [null, ''],
  ['building', 'sr'],
  ['noise_TRAIN_DAY', 'dBA'],
  ['sun-2018-03-21 08:00:00+01:00', 'lx'],
  ['connectivity_BALCONY_distance', ''],
])('for given %s dimension returns %s unit', (dimension, result) => {
  expect(HeatmapStatisticsUtils.getSimulationUnitByDimension(dimension)).toBe(result);
});

it.each([
  [[1, 2, 3, 4, 5], 'building', [0, 5, 3]],
  [[1, 2, 3, 4, 5], 'noise_TRAIN_DAY', [0, 60, 30]],
  [[0.05, 0.04, 0.03, 0.02, 0.01], 'sun-2018-03-21 08:00:00+01:00', [0, 0.05, 0.03]],
  [[0.05, 0.04, 0.03, 0.02, 0.01], 'connectivity_BALCONY_distance', [0, 0.05, 0.03]],
  [[0.005, 0.004, 0.003, 0.002, 0.001], 'railway_tracks', [0, 0.005, 0.003]],
  [[0.005, 0.004, 0.003, 0.002, 0.001], 'water', [0, 0.005, 0.003]],
  [[0, 0, 0, 0, 0], 'water', [0, DEFAULT_SPHERICAL_MAX, 0]],
  [[0.00001, 0.00001, 0.00001, 0.00001, 0.00001], 'water', [0, SPHERICAL_MAX_MIN, 0.00001]],
])('for given %s heatmap and %s dimension returns %s points', (heatmap, dimension, result) => {
  expect(HeatmapStatisticsUtils.getSimulationMeaningfulPoints(heatmap, dimension)).toEqual(result);
});

it.each([
  [[1, 2, 3, 4, 5], 3, 1.58],
  [[0.05, 0.04, 0.03, 0.02, 0.01], 0.03, 0.015],
])('for given %s population and %s mean returns %s standard deviation', (population, mean, result) => {
  expect(HeatmapStatisticsUtils._calculateStandardDeviation(population, mean)).toBeCloseTo(result, 2);
});

it.each([
  ['building', [1, 5], [1, 5]],
  ['noise_TRAIN_DAY', [1, 5], [1, 5]],
  ['sun-2018-03-21 08:00:00+01:00', [1, 5], [1000, 5000]],
  ['connectivity_BALCONY_distance', [1, 5], [1, 5]],
])(
  'for given %s dimension and %s min/max returns %s converted min/max',
  (dimension, minMax: [number, number], result) => {
    expect(HeatmapStatisticsUtils.convertMinMaxByDimension(dimension, minMax)).toEqual(result);
  }
);
