import React from 'react';
import { connect } from 'react-redux';
import { COLORS } from '../../constants';
import { Selection } from '../../types';
import './copyPasteSelection.css';
import { getCopyPasteSelectionValues } from './copyPasteSelection';

type RectangleToolSelectionProps = {
  selection: Selection;
  isDrawing: boolean;
  isDragging: boolean;
};

const RectangleToolSelection = ({ selection, isDrawing }: RectangleToolSelectionProps) => {
  if (!selection) return null;
  const { startPosition, endPosition } = selection;
  if (!startPosition || !endPosition || startPosition.x === -1 || endPosition.x === -1) return null;
  if (startPosition.x === endPosition.x && startPosition.y === endPosition.y) return null;

  const { x, y, width, height } = getCopyPasteSelectionValues({
    startPosition,
    endPosition,
    draggingPosition: undefined,
  });

  const selectionComplete = !isDrawing;

  return (
    <g data-testid="rectangle-tool-selection" transform={`translate(${x}, ${y})`}>
      <rect
        id="rectangle-tool-selection"
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
    </g>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const isDrawing = state.rectangleTool.drawing;
  const selection = state.rectangleTool.selection;
  return {
    isDrawing,
    selection,
  };
}

export default connect(mapStateToProps)(RectangleToolSelection);
