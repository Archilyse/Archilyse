import { SIMULATION_TYPES } from '../../../types';
import type { HeatmapStatistics } from '../components/StatisticsInfo';

class HeatmapStatisticsUtils {
  static getSimulationMeaningfulPoints = (heatmap: number[], dimension: string): [number, number, number] => {
    const sphericalMax = 1.5;

    let min = Math.min(...heatmap);
    let max = Math.max(...heatmap);
    let mean = HeatmapStatisticsUtils._calculateMean(heatmap);

    if (dimension.startsWith(SIMULATION_TYPES.NOISE)) {
      min = 0;
      max = 60;
      mean = 30;
    }

    if (!dimension.startsWith(SIMULATION_TYPES.CONNECTIVITY) && max < sphericalMax) {
      max = sphericalMax;
    }

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
    const decimals = HeatmapStatisticsUtils._getDecimalsNumberByDimension(dimension);

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

  static _getDecimalsNumberByDimension = (dimension: string): number => {
    if (!dimension) return 1;

    if (dimension.startsWith(SIMULATION_TYPES.SUN)) return 0;
    if (dimension.startsWith(SIMULATION_TYPES.NOISE)) return 0;
    if (dimension.startsWith(SIMULATION_TYPES.CONNECTIVITY)) return 2;
    return 1; // 'VIEW' dimension
  };
}

export default HeatmapStatisticsUtils;
