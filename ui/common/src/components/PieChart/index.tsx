import React, { useEffect, useState } from 'react';
import { VictoryLabel, VictoryPie } from 'victory';
import C from '../../constants';
import './pieChart.scss';

const PIE_HEIGHT = 200.2;
const PIE_WIDTH = 200.3;
const DEFAULT_PIE_INNER_RADIUS = 70;

// @TODO: Use constants here
const DEFAULT_LABEL_STYLE = {
  fontSize: '20px',
  fontFamily: 'Barlow Semi Condensed',
  fontWeight: 300,
  lineHeight: '48px',
  fill: C.COLORS.SECONDARY,
};

const parseLabel = (yValue: number): string => `${parseFloat(yValue.toFixed(1))}%`;
const DEFAULT_ANIMATION_BEHAVIOUR = {};

const PieChart = ({
  data,
  animate = false,
  colorFunction = null,
  onMouseOver = (dataSource: any): any => {},
  onMouseOut = (dataSource: any): any => {},
  showLabelByDefault = false,
  innerLabel = null,
  innerRadius = null,
  labelStyle = {},
}) => {
  const [label, setLabel] = useState<string>();
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    setAngle(1);
    setTimeout(() => {
      setAngle(360);
    }, 500);
  }, []);

  useEffect(() => {
    if (showLabelByDefault) {
      setLabel(parseLabel(data[0].y));
    }
  }, [data]);

  const labelText = innerLabel || label;
  if (!angle) return null; // Needed explicitly this avoid weird behaviour: https://github.com/facebook/react/issues/15281#issuecomment-480308487
  return (
    <svg viewBox={`0 0 ${PIE_HEIGHT} ${PIE_WIDTH}`}>
      <VictoryPie
        standalone={false}
        height={PIE_HEIGHT}
        width={PIE_WIDTH}
        data={data}
        endAngle={angle}
        animate={animate ? DEFAULT_ANIMATION_BEHAVIOUR : undefined}
        events={[
          {
            target: 'data',
            eventHandlers: {
              onMouseOver: () => ({
                mutation: dataSource => {
                  if (!innerLabel) setLabel(parseLabel(dataSource.datum.y));
                  // If the function has a return value
                  if (onMouseOver(dataSource)) {
                    return onMouseOver(dataSource);
                  }
                  onMouseOver(dataSource);
                },
              }),
              onMouseOut: () => ({
                mutation: dataSource => {
                  if (!showLabelByDefault && !innerLabel) {
                    setLabel('');
                  }
                  onMouseOut(dataSource);
                },
              }),
            },
          },
        ]}
        style={{
          data: {
            ...(colorFunction && { fill: colorFunction }),
            fillOpacity: 1,
            stroke: 'white',
            strokeWidth: 3,
          },
          labels: { fontSize: 8, fontFamily: 'Barlow' },
        }}
        innerRadius={innerRadius ? innerRadius : DEFAULT_PIE_INNER_RADIUS}
        labels={() => null}
      />
      {labelText && (
        <VictoryLabel
          textAnchor="middle"
          style={{ ...DEFAULT_LABEL_STYLE, ...labelStyle }}
          x={PIE_HEIGHT / 2}
          y={PIE_WIDTH / 2}
          text={labelText}
        />
      )}
    </svg>
  );
};

export default PieChart;
