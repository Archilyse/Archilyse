import React from 'react';
import { connect } from 'react-redux';
import * as GeometryUtils from '../../utils/geometry';
import { ProviderHash } from '../../providers';
import { MODE_COPY_PASTE, SeparatorsType } from '../../constants';
import getSelectedAnnotationsSize from '../../utils/get-selected-annotations-size';
import Ruler from './ruler';

const UNIT_M = 'm';

const countScaledToolLines = layer => {
  const allLines = Object.values(layer.lines);
  return allLines.filter(line => line.type === SeparatorsType.SCALE_TOOL).length;
};

const Line = ({ line, layer, scene, catalog, scaleTool, shouldRenderRuler }) => {
  const vertex0 = layer.vertices[line.vertices[0]];
  const vertex1 = layer.vertices[line.vertices[1]];
  const [{ x: x1, y: y1 }, { x: x2, y: y2 }] = GeometryUtils.orderVertices([vertex0, vertex1]);

  const length = GeometryUtils.pointsDistance(x1, y1, x2, y2);
  if (length == 0) {
    return null;
  }

  const holes = line.holes.map(holeID => {
    const hole = layer.holes[holeID];
    if (hole?.coordinates.length > 0) {
      const renderedHole = catalog.getElement(hole.type).render2D(hole, layer, scene);
      return (
        <g
          key={holeID}
          data-element-root
          data-prototype={hole.prototype}
          data-element-type={hole.type}
          data-id={hole.id}
          data-testid={`hole-${hole.id}`}
          data-selected={hole.selected}
          data-layer={layer.id}
        >
          {renderedHole}
        </g>
      );
    }
    return null;
  });

  const lineType = line.type;
  const angle = GeometryUtils.angleBetweenTwoPointsAndOrigin(x1, y1, x2, y2);
  const lineWidthInCM = line.properties.width.value;
  const lineWidthInPixels = GeometryUtils.convertCMToPixels(scene.scale, lineWidthInCM);
  const halfWidthInPixels = lineWidthInPixels / 2;
  const renderedLine = catalog.getElement(line.type).render2D(line, layer, scene);

  const scalingWithOneLine = line.type === SeparatorsType.SCALE_TOOL && countScaledToolLines(layer) === 1;

  const renderedRuler =
    line.selected || scalingWithOneLine ? (
      <Ruler
        scalingWithOneLine={scalingWithOneLine}
        scaleTool={scaleTool}
        unit={scalingWithOneLine ? UNIT_M : scene.unit}
        length={length}
        transform={`translate(0, ${halfWidthInPixels + 10} )`}
        scale={scene.scale}
      />
    ) : null;

  const [[x1p, y1p]] = GeometryUtils.getLinePointsFromReferenceLine(
    { x1, x2, y1, y2 },
    line.properties.referenceLine,
    lineWidthInPixels
  );

  return (
    <g
      data-testid={`viewer-line-${line.id}`}
      data-element-type={lineType}
      data-element-root
      data-prototype={line.prototype}
      data-id={line.id}
      data-selected={line.selected}
      data-layer={layer.id}
    >
      {renderedLine}
      {holes}
      {shouldRenderRuler && (
        <g className="ruler" transform={`translate(${x1p}, ${y1p}) rotate(${angle}, 0, 0)`}>
          {renderedRuler}
        </g>
      )}
    </g>
  );
};

export function areEqual(prevProps, nextProps) {
  const isCopyPasting =
    prevProps.draggingCopyPaste ||
    nextProps.draggingCopyPaste ||
    prevProps.rotatingCopyPaste ||
    nextProps.rotatingCopyPaste;

  if (
    isCopyPasting &&
    nextProps.selection &&
    nextProps.selection.lines &&
    nextProps.selection.lines.includes(nextProps.line.id)
  ) {
    return false;
  }

  //  Check if the line property is changed
  if (prevProps.line !== nextProps.line) {
    return false;
  }

  // If we are on scale tool line we want always to re-render to show the ruler updated
  if (nextProps.line.type === SeparatorsType.SCALE_TOOL) {
    return false;
  }
  // Check if the scene scale is changed
  if (prevProps.scene.scale !== nextProps.scene.scale) {
    return false;
  }

  // Check if the scene unit is changed
  if (prevProps.scene.unit !== nextProps.scene.unit) {
    return false;
  }

  // Check if shouldRenderRuler
  if (prevProps.shouldRenderRuler !== nextProps.shouldRenderRuler) {
    return false;
  }

  //  Check if the holes have changed (cheaper/simpler than comparing previous & next line holes in most cases)
  if (prevProps.layer.holes !== nextProps.layer.holes) {
    return false;
  }
  return true;
}

function mapStateToProps(state) {
  state = state['react-planner'];
  const { mode, scaleTool, copyPaste } = state;
  const isCopyPasteMode = mode === MODE_COPY_PASTE;
  const selectedAnnotationsSize = getSelectedAnnotationsSize(state);
  // only if one line is selected or if selected mode is COPY/PASTE
  const shouldRenderRuler = selectedAnnotationsSize < 2 || isCopyPasteMode;
  return {
    scaleTool,
    draggingCopyPaste: copyPaste.dragging,
    rotatingCopyPaste: copyPaste.rotating,
    isDrawing: copyPaste.drawing,
    selection: copyPaste.selection,
    shouldRenderRuler,
  };
}

const L = connect(mapStateToProps, {})(React.memo(Line, areEqual));
export default L;
