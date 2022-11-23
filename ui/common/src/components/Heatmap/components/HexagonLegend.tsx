import React from 'react';
import cn from 'classnames';
import { HeatmapProps } from '..';
import { calculateDomain } from '../../SimulationViewer/libs/SimRenderer';

const LEGEND_HEIGHT_BY_SIZE: Record<HeatmapProps['infoSize'], number> = {
  medium: 200,
  small: 120,
};

const HexagonLegend = ({ min, max, widthPx, size, renderLegend, unit = '' }) => {
  const legendHeight = LEGEND_HEIGHT_BY_SIZE[size];
  const domainFunction = calculateDomain(min, max);
  const numValues = 6;
  const numCells = 40;

  const calculateCellStyle = i => {
    return {
      backgroundColor: domainFunction(min + ((max - min) * (numCells - i)) / numCells),
      width: widthPx,
      height: legendHeight / numCells,
    };
  };

  const calculateLabelStyle = i => {
    return { top: ((legendHeight - 4) * (numValues - i)) / numValues };
  };

  const calculateLegend = i => {
    const value = min + ((max - min) * i) / numValues;

    return renderLegend(value, i, numValues);
  };

  return (
    <div className={cn('hexagon-legend', size)}>
      <div className="legend-cells">
        {[...Array(numCells)].map((e, i) => (
          <div style={calculateCellStyle(i)} className="legend-cell" key={i} />
        ))}
      </div>
      <div className="legend-values" style={{ left: widthPx }}>
        {[...Array(numValues + 1)].map((e, i) => (
          <div className="legend-value" key={i} style={calculateLabelStyle(i)}>
            {calculateLegend(i)}
          </div>
        ))}
      </div>
      {unit && <div className="unit-values">Values = {unit}</div>}
    </div>
  );
};

export default HexagonLegend;
