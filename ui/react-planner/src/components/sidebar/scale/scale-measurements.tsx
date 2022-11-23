import React, { useState } from 'react';
import { AiOutlineDown, AiOutlineRight } from 'react-icons/ai';
import { COLORS, SCALING_REQUIRED_MEASUREMENT_COUNT } from '../../../constants';
import ScaleMeasurement from '../../../types/ScaleMeasurement';
import FloorMeasures from '../FloorMeasures';
import { toFixedFloat } from '../../../utils/math';
import { calculateScale, isMeasurementOutlier } from './utils';

export const OUTLIER_STYLE = { color: COLORS.INVALID, cursor: 'pointer', fontWeight: 'bold' };
export const VALID_STYLE = { color: COLORS.VALID, cursor: 'pointer', margin: 0 };

const LIST_ELEMENT_STYLE = {
  display: 'flex',
  justifyContent: 'space-between',
  alignContent: 'baseline',
  alignItems: 'baseline',
};

const PARAGRAPH_STYLE = { marginTop: '5px', marginBottom: '5px' };

const ScaleMeasurements = ({ floorScales, floorScalesRequest, scaleTool, measurements }) => {
  const [selectedMeasurement, setSelectedMeasurement] = useState<ScaleMeasurement>();
  const { points: currentPoints } = scaleTool;

  const isSelected = measure => measure.points.join(',') === selectedMeasurement?.points?.join(',');

  const measuresToTake = Array.from(Array(SCALING_REQUIRED_MEASUREMENT_COUNT).keys());
  return (
    <>
      <ul>
        {measuresToTake.map(number => {
          const measure = measurements[number];
          const isOutlier = isMeasurementOutlier(measurements, measure) && number === measurements.length - 1;
          const measureNumber = number + 1; // So we don't show measure #0 to the users

          if (measure) {
            return (
              <li
                key={`measurement-${measureNumber}`}
                style={isOutlier ? OUTLIER_STYLE : VALID_STYLE}
                onClick={() => (isSelected(measure) ? setSelectedMeasurement(null) : setSelectedMeasurement(measure))}
              >
                <div style={{ ...LIST_ELEMENT_STYLE }}>
                  <p style={{ ...PARAGRAPH_STYLE }}>
                    Measurement #{measureNumber}: Scale {'-> '} {toFixedFloat(calculateScale(measure), 2)}
                  </p>
                  {isSelected(measure) ? <AiOutlineDown /> : <AiOutlineRight />}
                </div>
              </li>
            );
          }
          return (
            <li key={`measurement-${measureNumber}`}>
              <div style={{ ...LIST_ELEMENT_STYLE }}>
                <p style={{ ...PARAGRAPH_STYLE }}>Measurement #{measureNumber}:</p>
              </div>
            </li>
          );
        })}
      </ul>
      {selectedMeasurement && (
        <FloorMeasures
          floorScales={floorScales}
          points={selectedMeasurement ? selectedMeasurement.points : currentPoints}
          requestStatus={floorScalesRequest}
        />
      )}
    </>
  );
};

export default ScaleMeasurements;
