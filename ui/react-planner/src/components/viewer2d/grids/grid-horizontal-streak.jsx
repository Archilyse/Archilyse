import React from 'react';
import PropTypes from 'prop-types';

export default function GridHorizontalStreak({ width, height, grid }) {
  const step = grid.properties.step;
  let colors;

  if (grid.properties.color) {
    colors = [grid.properties.color];
  } else {
    colors = grid.properties.colors;
  }

  const rendered = [];
  let i = 0;
  for (let y = 0; y <= height; y += step) {
    const color = colors[i % colors.length];
    i++;
    rendered.push(<line key={y} x1="0" y1={y} x2={width} y2={y} strokeWidth="1" stroke={color} />);
  }

  return <g id="GridHorizontalStreak">{rendered}</g>;
}

GridHorizontalStreak.propTypes = {
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
  grid: PropTypes.object.isRequired,
};
