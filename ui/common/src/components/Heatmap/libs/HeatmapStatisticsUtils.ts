import { SIMULATION_TYPES } from '../../../types';
import type { HeatmapStatistics } from '../components/StatisticsInfo';

export const DEFAULT_SPHERICAL_MAX = 1.5;
export const SPHERICAL_MAX_MIN = 0.005;

const countDecimals = (value: number) => value?.toString().split('.')[1]?.length || 0;
const isDimensionWithLowValues = value => {
  console.log('value', value < 0, countDecimals(value) > 2);
  return value < 1 && countDecimals(value) > 2;
};

class HeatmapStatisticsUtils {
  static getSimulationMeaningfulPoints = (heatmap: number[], dimension: string): [number, number, number] => {
    let min = Math.min(...heatmap);
    let max = Math.max(...heatmap);
    let mean = HeatmapStatisticsUtils._calculateMean(heatmap);

    if (dimension.startsWith(SIMULATION_TYPES.NOISE)) {
      min = 0;
      max = 60;
      mean = 30;
    }

    // If no data/values, we apply a default max so heatmaps looks blue
    if (max === 0) max = DEFAULT_SPHERICAL_MAX;
    else if (!dimension.startsWith(SIMULATION_TYPES.CONNECTIVITY) && max <= SPHERICAL_MAX_MIN) max = SPHERICAL_MAX_MIN;

    // should be <= 0
    if (min > 0) min = 0;

    return [min, max, mean];
  };

  static calculateSimulationDistribution = (
    heatmap: number[],
    [min, max, mean]: [number, number, number]
  ): HeatmapStatistics => {
    const std = HeatmapStatisticsUtils._calculateStandardDeviation(heatmap, mean);

    return {
      max,
      min,
      average: mean,
      std,
    };
  };

  static getSimulationUnitByDimension = (dimension: string): string => {
    if (!dimension) return '';

    if (dimension.startsWith(SIMULATION_TYPES.SUN)) return 'lx';
    if (dimension.startsWith(SIMULATION_TYPES.NOISE)) return 'dBA';
    if (dimension.startsWith(SIMULATION_TYPES.CONNECTIVITY)) return ''; // hard to say what unit connectivity should have so far
    return 'sr'; // 'VIEW' dimension
  };

  static convertMinMaxByDimension = (dimension: string, [min, max]: [number, number]): [number, number] => {
    let _min = min;
    let _max = max;

    if (dimension.startsWith(SIMULATION_TYPES.SUN)) {
      const KLUX_TO_LUX_CONVERSION = 1000;
      _min = Math.abs(min * KLUX_TO_LUX_CONVERSION);
      _max = Math.abs(max * KLUX_TO_LUX_CONVERSION);
    }

    return [_min, _max];
  };

  static formatLegendByDimension = (dimension: string) => (
    value: number,
    index: number,
    allValuesNumber: number
  ): string => {
    const decimals = HeatmapStatisticsUtils._getDecimalsNumberByDimension(dimension, value);

    if (dimension.startsWith(SIMULATION_TYPES.NOISE) && index === allValuesNumber) {
      return `> ${value.toFixed(decimals)}`;
    }

    return value.toFixed(decimals);
  };

  static _calculateMean = (populations: number[]): number => {
    return (populations || []).reduce((a, b) => a + b, 0) / populations.length;
  };

  static _calculateStandardDeviation = (populations: number[], mean: number): number => {
    return Math.sqrt(populations.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / (populations.length - 1));
  };

  static _getDecimalsNumberByDimension = (dimension: string, value: number): number => {
    if (!dimension) return 1;

    if (dimension.startsWith(SIMULATION_TYPES.SUN)) return 0;
    if (dimension.startsWith(SIMULATION_TYPES.NOISE)) return 0;
    if (dimension.startsWith(SIMULATION_TYPES.CONNECTIVITY)) return 2;
    if (isDimensionWithLowValues(value)) return 4;
    return 1; // 'VIEW' dimension
  };
}

export default HeatmapStatisticsUtils;
