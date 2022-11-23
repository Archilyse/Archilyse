import React from 'react';
import { connect } from 'react-redux';
import { COLORS } from '../../constants';
import { Selection } from '../../types';
import * as GeometryUtils from '../../utils/geometry';
import './copyPasteSelection.css';
import { RotationCircle } from './rotationCircle';

type CopyPasteSelectionProps = {
  selection: Selection;
  isDrawing: boolean;
  isDragging: boolean;
};

export const getCopyPasteSelectionValues = ({ startPosition, endPosition, draggingPosition }) => {
  const { x, y, width, height } = GeometryUtils.getRectParametersFromSelection({
    startPosition,
    endPosition,
    draggingPosition,
  });
  const halfWidth = width / 2;
  const halfHeight = height / 2;

  return { x, y, width, height, halfWidth, halfHeight };
};

const copyPasteSelection = ({ selection, isDrawing, isDragging }: CopyPasteSelectionProps) => {
  if (!selection) return null;
  const { startPosition, endPosition, draggingPosition, rotation = 0 } = selection;
  if (!startPosition || !endPosition || startPosition.x === -1 || endPosition.x === -1) return null;
  if (startPosition.x === endPosition.x && startPosition.y === endPosition.y) return null;

  const { x, y, width, height, halfWidth, halfHeight } = getCopyPasteSelectionValues({
    startPosition,
    endPosition,
    draggingPosition,
  });

  const selectionComplete = !isDrawing;
  const rotationCircleRadius = 0.5 * Math.sqrt(width ** 2 + height ** 2);

  let cursor;
  if (selectionComplete) {
    cursor = isDragging ? 'grabbing' : 'grab';
  }

  return (
    <g
      data-testid="copy-paste-selection"
      transform={`translate(${x}, ${y}) rotate(${rotation}, ${halfWidth}, ${halfHeight})`}
    >
      <rect
        id="copy-paste-selection"
        style={{ cursor }}
        className={selectionComplete ? 'selectionComplete' : ''}
        fill={'black'}
        fillOpacity={0.2}
        stroke={COLORS.PRIMARY_COLOR}
        strokeWidth="2px"
        strokeDasharray={`${selectionComplete ? '10,10' : 'none'}`}
        width={width}
        height={height}
        x={0}
        y={0}
      />
      {selectionComplete && (
        <RotationCircle width={halfWidth} height={halfHeight} rotationCircleRadius={rotationCircleRadius} />
      )}
    </g>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const isDragging = state.copyPaste.dragging;
  const isDrawing = state.copyPaste.drawing;
  const selection = state.copyPaste.selection;
  return {
    isDragging,
    isDrawing,
    selection,
  };
}

export default connect(mapStateToProps)(copyPasteSelection);
