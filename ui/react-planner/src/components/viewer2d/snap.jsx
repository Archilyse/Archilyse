import React from 'react';
import PropTypes from 'prop-types';

const STYLE = {
  stroke: '#D32F2F',
  strokeWidth: '1px',
};

const ActiveDrawingHelper = ({ snap }) => {
  const snapStyle = snap.metadata && snap.metadata.style;

  switch (snap.type) {
    case 'point':
      return (
        <g data-testid="snap-element" transform={`translate(${snap.x} ${snap.y})`}>
          <line x1="0" y1="-5" x2="0" y2="5" style={STYLE} />
          <line x1="-5" y1="0" x2="5" y2="0" style={STYLE} />
        </g>
      );
    case 'line-segment':
      return (
        <line
          data-testid="snap-element"
          x1={snap.x1}
          y1={snap.y1}
          x2={snap.x2}
          y2={snap.y2}
          style={{ ...STYLE, ...snapStyle }}
        />
      );

    default:
      return null;
  }
};

ActiveDrawingHelper.propTypes = {
  snap: PropTypes.object.isRequired,
};

export default ActiveDrawingHelper;
