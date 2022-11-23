import React from 'react';
import PropTypes from 'prop-types';

export default function GridVerticalStreak({ width, height, grid }) {
  const step = grid.properties.step;
  let colors;

  if (grid.properties.color) {
    colors = [grid.properties.color];
  } else {
    colors = grid.properties.colors;
  }

  const rendered = [];
  let i = 0;
  for (let x = 0; x <= width; x += step) {
    const color = colors[i % colors.length];
    i++;
    rendered.push(<line key={x} x1={x} y1="0" x2={x} y2={height} strokeWidth="1" stroke={color} />);
  }

  return <g>{rendered}</g>;
}

GridVerticalStreak.propTypes = {
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
  grid: PropTypes.object.isRequired,
};
