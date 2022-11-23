import React from 'react';
import { HeatmapProps } from '..';
import HeatmapStatisticsUtils from '../libs/HeatmapStatisticsUtils';
import HexagonLegend from './HexagonLegend';
import NorthArrow from './NorthArrow';
import './statisticsInfo.scss';

export type HeatmapStatistics = {
  min: number;
  max: number;
  average: number;
  std: number;
};

type Props = {
  statistics: HeatmapStatistics;
  simulationName: string;
  size: HeatmapProps['infoSize'];
};

const StatisticsInfo = ({ statistics, simulationName, size }: Props): JSX.Element => {
  const NORTH_ANGLE_ORIENTATION = 0;

  const simulationUnit = HeatmapStatisticsUtils.getSimulationUnitByDimension(simulationName);
  const [min, max] = HeatmapStatisticsUtils.convertMinMaxByDimension(simulationName, [statistics.min, statistics.max]);

  return (
    <>
      <HexagonLegend
        size={size}
        widthPx={15}
        min={min}
        max={max}
        unit={simulationUnit}
        renderLegend={HeatmapStatisticsUtils.formatLegendByDimension(simulationName)}
      />
      <NorthArrow angle={NORTH_ANGLE_ORIENTATION} size={size} />
    </>
  );
};

export default StatisticsInfo;
