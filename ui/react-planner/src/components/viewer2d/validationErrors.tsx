import React from 'react';
import { ValidationError } from '../../types';
import { getValidationErrorColor } from '../../utils/export';

// @TODO: Pointer events are "covered" by the enclosing area so for now we can not
// put the functionality of hovering + higlight without disabling clicks on an area
const ValidationErrors = ({ errors, highlightedError }) => {
  const errorList: ValidationError[] = errors;

  return (
    <g pointerEvents={'all'}>
      {errorList.map((error, index) => {
        const { position, object_id, is_blocking } = error;

        const [x, y] = position.coordinates;
        const radius = object_id === highlightedError ? 100 : 40;
        const fill = getValidationErrorColor(is_blocking, object_id, highlightedError);
        const fillOpacity = 0.5;
        const translateY = y - 15; // 20 ~= (fontSize / 2 - 5)
        const errorNumber = index + 1;
        return (
          <g key={object_id}>
            <circle
              cx={x}
              cy={y}
              r={radius}
              id={`error-circle-${errorNumber}`}
              data-testid={`error-circle-${errorNumber}`}
              strokeWidth="0"
              fill={fill}
              fillOpacity={fillOpacity}
            />
            <text
              transform={`translate(${x},${translateY}) scale(1,-1)`}
              style={{ textAnchor: 'middle', fontSize: '40px' }}
            >
              {errorNumber}
            </text>
          </g>
        );
      })}
    </g>
  );
};

export default ValidationErrors;
