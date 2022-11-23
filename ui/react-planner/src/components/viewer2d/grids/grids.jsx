import React from 'react';
import PropTypes from 'prop-types';
import GridHorizontalStreak from './grid-horizontal-streak';
import GridVerticalStreak from './grid-vertical-streak';

function Grids({ scene }) {
  const { width, height, grids } = scene;
  const renderedGrids = Object.entries(grids).map(([gridID, grid]) => {
    switch (grid.type) {
      case 'horizontal-streak':
        return <GridHorizontalStreak key={gridID} width={width} height={height} grid={grid} />;

      case 'vertical-streak':
        return <GridVerticalStreak key={gridID} width={width} height={height} grid={grid} />;

      default:
        console.warn(`grid ${grid.type} not allowed`);
    }
  });

  return <g>{renderedGrids}</g>;
}

Grids.propTypes = {
  scene: PropTypes.object.isRequired,
};

export const areEqual = (prevProps, nextProps) => {
  // Check if scene width has changed
  if (prevProps.scene.width !== nextProps.scene.width) {
    return false;
  }

  // Check if scene height has changed
  if (prevProps.scene.height !== nextProps.scene.height) {
    return false;
  }

  // Check if grids have changed
  if (prevProps.scene.grids !== nextProps.scene.grids) {
    return false;
  }

  return true;
};

export default React.memo(Grids, areEqual);
