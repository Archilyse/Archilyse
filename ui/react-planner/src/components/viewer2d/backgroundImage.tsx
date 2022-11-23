import React from 'react';
import { connect } from 'react-redux';
import { Background } from '../../types';
import { COLORS, MODE_ROTATE_SCALE_BACKGROUND } from '../../constants';

// We don't want the user to be able to drag the image
const onFloorplanImgMouseDown = event => event.preventDefault();

const getImagePosition = (sceneHeight, background: Background) => ({
  x: background.shift.x,
  y: sceneHeight - background.height - background.shift.y, // Y starts at the bottom of the scene
});

const BackgroundImage = ({ floorplanImgUrl, mode, sceneHeight, background: originalBackground }) => {
  const background = { ...originalBackground }; // As by default immer enforces freeze on every object in the result state to avoid side effects
  background.shift = {
    x: background.shift?.x || 0,
    y: background.shift?.y || 0,
  };

  const { x, y } = getImagePosition(sceneHeight, background);
  const pointToRotate = { x: background.width / 2 + x, y: background.height / 2 + y };
  return (
    <g
      data-testid="background-img-group"
      id="background-img-group"
      transform={`rotate(${background.rotation}, ${pointToRotate.x}, ${pointToRotate.y})`}
    >
      <image
        onMouseDown={onFloorplanImgMouseDown}
        data-testid="floorplan-img"
        id="floorplan-img"
        preserveAspectRatio="none"
        href={floorplanImgUrl}
        x={x}
        y={y}
        width={background.width}
        height={background.height}
      />
      {mode === MODE_ROTATE_SCALE_BACKGROUND && (
        <rect
          fill={'black'}
          fillOpacity={0.1}
          stroke={COLORS.PRIMARY_COLOR}
          strokeWidth="10px"
          width={background.width}
          height={background.height}
          x={x}
          y={y}
        />
      )}
    </g>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const { floorplanImgUrl, mode } = state;
  const sceneHeight = state.scene.height;
  const background: Background = state.scene.background;
  return {
    floorplanImgUrl,
    mode,
    sceneHeight,
    background,
  };
}

export default connect(mapStateToProps)(BackgroundImage);
