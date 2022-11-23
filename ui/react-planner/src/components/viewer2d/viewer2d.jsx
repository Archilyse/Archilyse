import React, { useEffect } from 'react';
import cn from 'classnames';
import { connect } from 'react-redux';
import * as constants from '../../constants';
import * as SharedStyle from '../../shared-style';
import { useCheckUnsavedChanges } from '../../hooks/export';
import { hasProjectChanged } from '../../utils/export';
import RulerX from './rulerX';
import RulerY from './rulerY';
import State from './state';
import SvgPanZoom from './svgPanZoom';

const { INITIAL_SCENE_WIDTH } = constants;

function mode2PointerEvents(mode) {
  switch (mode) {
    case constants.MODE_DRAWING_LINE:
    case constants.MODE_DRAWING_HOLE:
    case constants.MODE_DRAWING_ITEM:
    case constants.MODE_DRAGGING_HOLE:
    case constants.MODE_DRAGGING_ITEM:
    case constants.MODE_DRAGGING_VERTEX:
      return { pointerEvents: 'none' };

    default:
      return {};
  }
}

function mode2Cursor(mode) {
  switch (mode) {
    case constants.MODE_DRAGGING_HOLE:
    case constants.MODE_DRAGGING_VERTEX:
    case constants.MODE_DRAGGING_ITEM:
      return { cursor: 'move' };

    case constants.MODE_ROTATING_ITEM:
      return { cursor: 'ew-resize' };

    case constants.MODE_RECTANGLE_TOOL:
    case constants.MODE_WAITING_DRAWING_LINE:
    case constants.MODE_DRAWING_LINE:
    case constants.MODE_COPY_PASTE:
      return { cursor: 'crosshair' };
    default:
      return { cursor: 'default' };
  }
}

const Viewer2D = ({ width, height, mode, floorplanImgUrl, sceneWidth, sceneHeight, projectHasChanges }) => {
  useCheckUnsavedChanges(projectHasChanges);
  useEffect(() => {
    // to prevent Chrome of zoom-(in/out) the whole page when you hold `ctrl` and scroll
    // it doesn't work in Firefox :/
    const handler = event => {
      if (event.ctrlKey) event.preventDefault();
    };

    window.addEventListener('mousewheel', handler, { passive: false });

    return () => {
      window.removeEventListener('mousewheel', handler);
    };
  }, []);

  const rulerSize = 15; //px
  const rulerUnitPixelSize = 100;
  const rulerBgColor = SharedStyle.PRIMARY_COLOR.main;
  const rulerFnColor = SharedStyle.COLORS.white;
  const rulerMkColor = SharedStyle.SECONDARY_COLOR.main;
  const rulerXElements = Math.ceil(sceneWidth / rulerUnitPixelSize) + 1;
  const rulerYElements = Math.ceil(sceneHeight / rulerUnitPixelSize) + 1;

  const viewerClassname = cn({ 'floorplan-img-loaded': floorplanImgUrl, centered: sceneWidth !== INITIAL_SCENE_WIDTH });
  return (
    <div
      id="viewer"
      data-testid={floorplanImgUrl ? `viewer-${sceneWidth}x${sceneHeight}` : ''}
      className={viewerClassname}
      style={{
        margin: 0,
        padding: 0,
        display: 'grid',
        gridRowGap: '0',
        gridColumnGap: '0',
        gridTemplateColumns: `${rulerSize}px ${width - rulerSize}px`,
        gridTemplateRows: `${rulerSize}px ${height - rulerSize}px`,
        position: 'relative',
      }}
    >
      <div style={{ gridColumn: 1, gridRow: 1, backgroundColor: rulerBgColor }}></div>
      <SvgPanZoom width={width} height={height}>
        <svg data-testid="svg-pan" width={sceneWidth || width} height={sceneHeight || height}>
          <defs>
            <pattern id="diagonalFill" patternUnits="userSpaceOnUse" width="4" height="4" fill="#FFF">
              <rect x="0" y="0" width="4" height="4" fill="#FFF" />
              <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2" style={{ stroke: '#8E9BA2', strokeWidth: 1 }} />
            </pattern>
          </defs>
          <g style={Object.assign(mode2Cursor(mode), mode2PointerEvents(mode))}>
            <State />
          </g>
        </svg>
        {/* {sceneHeight ? (
          <svg data-testid="svg-pan" width={sceneWidth} height={sceneHeight}>
            <defs>
              <pattern id="diagonalFill" patternUnits="userSpaceOnUse" width="4" height="4" fill="#FFF">
                <rect x="0" y="0" width="4" height="4" fill="#FFF" />
                <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2" style={{ stroke: '#8E9BA2', strokeWidth: 1 }} />
              </pattern>
            </defs>
            <g style={Object.assign(mode2Cursor(mode), mode2PointerEvents(mode))}>
              <State />
            </g>
          </svg>
        ): <svg></svg>} */}
      </SvgPanZoom>
      <div style={{ gridRow: 1, gridColumn: 2, position: 'relative', overflow: 'hidden' }} id="rulerX">
        {sceneWidth ? (
          <RulerX
            unitPixelSize={rulerUnitPixelSize}
            width={width - rulerSize}
            backgroundColor={rulerBgColor}
            fontColor={rulerFnColor}
            markerColor={rulerMkColor}
            positiveUnitsNumber={rulerXElements}
            negativeUnitsNumber={0}
          />
        ) : null}
      </div>
      <div style={{ gridColumn: 1, gridRow: 2, position: 'relative', overflow: 'hidden' }} id="rulerY">
        {sceneHeight ? (
          <RulerY
            unitPixelSize={rulerUnitPixelSize}
            height={height - rulerSize}
            backgroundColor={rulerBgColor}
            fontColor={rulerFnColor}
            markerColor={rulerMkColor}
            positiveUnitsNumber={rulerYElements}
            negativeUnitsNumber={0}
          />
        ) : null}
      </div>
    </div>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const projectHasChanges = hasProjectChanged(state);

  const { mode, floorplanImgUrl, scene } = state;

  const sceneWidth = scene.width;
  const sceneHeight = scene.height;

  return {
    mode,
    sceneWidth,
    sceneHeight,
    floorplanImgUrl,
    projectHasChanges,
  };
}

export default connect(mapStateToProps)(Viewer2D);
