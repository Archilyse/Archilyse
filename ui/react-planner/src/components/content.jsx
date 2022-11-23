import React from 'react';
import PropTypes from 'prop-types';
import * as constants from '../constants';
import Viewer2D from './viewer2d/viewer2d';

const Content = React.memo(({ width, height, mode }) => {
  switch (mode) {
    case constants.MODE_IDLE:
    case constants.MODE_RECTANGLE_TOOL:
    case constants.MODE_2D_ZOOM_IN:
    case constants.MODE_2D_ZOOM_OUT:
    case constants.MODE_2D_PAN:
    case constants.MODE_WAITING_DRAWING_LINE:
    case constants.MODE_DRAGGING_VERTEX:
    case constants.MODE_DRAGGING_ITEM:
    case constants.MODE_DRAWING_LINE:
    case constants.MODE_DRAWING_HOLE:
    case constants.MODE_DRAWING_ITEM:
    case constants.MODE_DRAGGING_HOLE:
    case constants.MODE_ROTATING_ITEM:
    case constants.MODE_HELP:
    case constants.MODE_COPY_PASTE:
    case constants.MODE_ROTATE_SCALE_BACKGROUND:
    case constants.MODE_IMPORT_ANNOTATIONS:
      return <Viewer2D width={width} height={height} />;

    default:
      throw new Error(`Mode ${mode} doesn't have a mapped content`);
  }
});

Content.propTypes = {
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
};

export default Content;
