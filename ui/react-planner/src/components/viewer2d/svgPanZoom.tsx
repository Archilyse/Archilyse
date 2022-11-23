import React, { useCallback, useEffect, useRef } from 'react';
import {
  ALIGN_CENTER,
  POSITION_NONE,
  TOOL_AUTO,
  TOOL_NONE,
  TOOL_PAN,
  TOOL_ZOOM_IN,
  TOOL_ZOOM_OUT,
  UncontrolledReactSVGPanZoom,
} from 'react-svg-pan-zoom';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import produce from 'immer';
import * as constants from '../../constants';
import { clickedInsideSelection } from '../../utils/export';
import actions from '../../actions/export';
import { objectsMap } from '../../utils/objects-utils';
import getSelectedAnnotationsSize from '../../utils/get-selected-annotations-size';
import { CopyPaste, RectangleSelectTool } from '../../class/export';
import { setCopyPasteSelectionTransform, updateSelectedAnnotations } from './svgPanZoom.utils';

const { INITIAL_SCENE_WIDTH, SVG_PLAN_CLASSNAME } = constants;
const rulerSize = 15; //px
const miniatureProps = { position: POSITION_NONE };
const toolbarProps = { position: POSITION_NONE };

const SvgPanZoom = React.memo(
  ({
    state,
    children,
    width,
    height,
    mode,
    alterate,
    layerID,
    snapMask,
    ctrlActive,
    sceneWidth,
    sceneHeight,

    rectangleToolDrawingSelection,
    rectangleToolSelection,

    drawingSelection,
    draggingSelection,
    rotatingSelection,
    copyPasteSelection,
    isPendingRequest,

    viewer2DActions,
    linesActions,
    holesActions,
    copyPasteActions,
    itemsActions,
    areaActions,
    projectActions,
    verticesActions,
    rectangleToolActions,
  }: any) => {
    const Viewer2DRef = useRef(null);
    const isCentered = state.centered;

    useEffect(() => {
      if (sceneWidth !== INITIAL_SCENE_WIDTH) {
        requestAnimationFrame(() => Viewer2DRef.current?.fitToViewer(ALIGN_CENTER, ALIGN_CENTER));
      }
    }, [sceneWidth, sceneHeight, isCentered]);

    const mapCursorPosition = ({ x, y }) => {
      return { x, y: -y + sceneHeight };
    };

    const onMouseMove = useCallback(
      viewerEvent => {
        //workaround that allow imageful component to work
        const evt = new Event('mousemove-planner-event');
        (evt as any).position = mapCursorPosition(viewerEvent);
        (evt as any).viewerEvent = viewerEvent;
        document.dispatchEvent(evt);

        const { x, y } = mapCursorPosition(viewerEvent);

        switch (mode) {
          case constants.MODE_DRAWING_LINE:
            linesActions.updateDrawingLine(x, y);
            break;

          case constants.MODE_DRAWING_HOLE:
            holesActions.updateDrawingHole(layerID, x, y);
            break;

          case constants.MODE_DRAWING_ITEM:
            itemsActions.updateDrawingItem(layerID, x, y);
            break;

          case constants.MODE_DRAGGING_HOLE:
            holesActions.updateDraggingHole(x, y);
            break;

          case constants.MODE_DRAGGING_VERTEX:
            verticesActions.updateDraggingVertex(x, y, state.snapMask);
            break;

          case constants.MODE_DRAGGING_ITEM:
            itemsActions.updateDraggingItem(x, y);
            break;

          case constants.MODE_ROTATING_ITEM:
            itemsActions.updateRotatingItem(x, y);
            break;
          case constants.MODE_COPY_PASTE: {
            produce(state, state => {
              const copyPasteElem = document.querySelector('g[data-testid="copy-paste-selection"]');
              if (drawingSelection) {
                if (copyPasteElem) {
                  const { updatedState } = CopyPaste.updateCopyPasteSelection(state, { payload: { x, y } });
                  setCopyPasteSelectionTransform({
                    copyPasteElem,
                    updatedState,
                    setRectangleDimensions: true,
                  });
                } else {
                  copyPasteActions.updateCopyPasteSelection(x, y);
                }
              } else if (draggingSelection) {
                const { updatedState } = CopyPaste.updateDraggingCopyPasteSelection(state, { payload: { x, y } });
                setCopyPasteSelectionTransform({
                  copyPasteElem,
                  updatedState,
                  setRectangleDimensions: false,
                });
                updateSelectedAnnotations({ updatedState });
              } else if (rotatingSelection) {
                const { updatedState } = CopyPaste.updateRotatingCopyPasteSelection(state, { payload: { x, y } });
                setCopyPasteSelectionTransform({
                  copyPasteElem,
                  updatedState,
                  setRectangleDimensions: false,
                });
                updateSelectedAnnotations({ updatedState });
              }
            });
            break;
          }
          case constants.MODE_RECTANGLE_TOOL:
            if (rectangleToolDrawingSelection) {
              const rectangleToolSelectionElem = document.querySelector('g[data-testid="rectangle-tool-selection"]');
              if (rectangleToolSelectionElem) {
                produce(state, state => {
                  const { updatedState } = RectangleSelectTool.updateRectangleSelection(state, { payload: { x, y } });
                  setCopyPasteSelectionTransform({
                    copyPasteElem: rectangleToolSelectionElem,
                    updatedState,
                    setRectangleDimensions: true,
                    selectionType: 'rectangleTool',
                  });
                });
              } else {
                rectangleToolActions.updateRectangleSelection(x, y);
              }
            }
            break;
        }

        viewerEvent.originalEvent.stopPropagation();
      },
      [
        snapMask,
        drawingSelection,
        draggingSelection,
        rotatingSelection,
        mode,
        copyPasteSelection,
        state,
        rectangleToolDrawingSelection,
        rectangleToolSelection,
      ]
    );

    const onMouseDown = useCallback(
      viewerEvent => {
        const event = viewerEvent.originalEvent;

        //workaround that allow imageful component to work
        const evt: any = new Event('mousedown-planner-event');
        evt.viewerEvent = viewerEvent;
        document.dispatchEvent(evt);

        const { x, y } = mapCursorPosition(viewerEvent);

        if (mode === constants.MODE_IDLE) {
          const elementData = extractElementData(event.target);
          if (!elementData || !elementData.selected) return;

          switch (elementData.prototype) {
            case 'vertices': {
              const selectedAnnotationsSize = getSelectedAnnotationsSize(state);
              const multipleSelected = selectedAnnotationsSize > 1;
              // Avoid dragging a vertex when multiple annotations are selected at once
              if (multipleSelected) {
                break;
              }

              const vertexId = elementData.id;
              const [selectedLineId] = state.scene.layers[layerID].selected.lines;
              const selectedLineMainVerticeIds = state.scene.layers[layerID].lines[selectedLineId].vertices;

              // is not auxiliary vertex clicked
              const isMainVertexClicked = selectedLineMainVerticeIds?.includes(vertexId);
              if (isMainVertexClicked) {
                verticesActions.beginDraggingVertex(elementData.layer, vertexId, x, y, state.snapMask);
              }
              break;
            }

            case 'items':
              if (!ctrlActive) {
                if (elementData.part === 'rotation-anchor')
                  itemsActions.beginRotatingItem(elementData.layer, elementData.id, x, y);
                else itemsActions.beginDraggingItem(elementData.layer, elementData.id, x, y);
              }
              break;

            case 'holes':
              if (!ctrlActive) {
                holesActions.beginDraggingHole(elementData.layer, elementData.id, x, y);
              }
              break;

            default:
              break;
          }
        } else if (mode === constants.MODE_COPY_PASTE) {
          if (clickedInsideSelection(x, y, copyPasteSelection)) {
            copyPasteActions.beginDraggingCopyPasteSelection(x, y);
          } else {
            const part = event.target.attributes.getNamedItem('data-part')?.value;
            if (part === 'rotation-anchor') {
              copyPasteActions.beginRotatingCopyPasteSelection(x, y);
            } else {
              copyPasteActions.beginCopyPasteSelection(x, y);
            }
          }
        } else if (mode === constants.MODE_RECTANGLE_TOOL) {
          rectangleToolActions.beginRectangleSelection(x, y);
        }
        event.stopPropagation();
      },
      [
        copyPasteSelection,
        ctrlActive,
        mode,
        rectangleToolDrawingSelection,
        rectangleToolSelection,
        sceneHeight,
        state.scene.layers[layerID].selected,
      ]
    );

    const onMouseUp = useCallback(
      viewerEvent => {
        const event = viewerEvent.originalEvent;
        const evt: any = new Event('mouseup-planner-event');
        evt.viewerEvent = viewerEvent;
        document.dispatchEvent(evt);

        const { x, y } = mapCursorPosition(viewerEvent);

        switch (mode) {
          case constants.MODE_IDLE: {
            const elementData = extractElementData(event.target);
            const isElementSelected = elementData && elementData.selected;
            const shouldUnselect = ctrlActive && isElementSelected;

            switch (elementData ? elementData.prototype : 'none') {
              case 'areas':
                if (shouldUnselect) {
                  areaActions.unselectArea(elementData.layer, elementData.id);
                } else {
                  areaActions.selectArea(elementData.layer, elementData.id);
                }
                break;

              case 'lines':
                if (shouldUnselect) {
                  linesActions.unselectLine(elementData.layer, elementData.id);
                } else {
                  linesActions.selectLine(elementData.layer, elementData.id);
                }
                break;

              case 'holes':
                if (shouldUnselect) {
                  holesActions.unselectHole(elementData.layer, elementData.id);
                } else {
                  holesActions.selectHole(elementData.layer, elementData.id);
                }
                break;

              case 'items':
                if (shouldUnselect) {
                  itemsActions.unselectItem(elementData.layer, elementData.id);
                } else {
                  itemsActions.selectItem(elementData.layer, elementData.id);
                }
                break;

              case 'none':
                projectActions.unselectAll();
                break;
            }
            break;
          }
          case constants.MODE_WAITING_DRAWING_LINE:
            linesActions.beginDrawingLine(layerID, x, y);
            break;

          case constants.MODE_DRAWING_LINE:
            linesActions.endDrawingLine(x, y);
            linesActions.beginDrawingLine(layerID, x, y);
            break;

          case constants.MODE_DRAWING_HOLE:
            holesActions.endDrawingHole(layerID, x, y);
            break;

          case constants.MODE_DRAWING_ITEM:
            itemsActions.endDrawingItem(layerID, x, y);
            break;

          case constants.MODE_DRAGGING_VERTEX:
            verticesActions.endDraggingVertex(x, y, state.snapMask);
            break;

          case constants.MODE_DRAGGING_ITEM:
            itemsActions.endDraggingItem(x, y);
            break;

          case constants.MODE_DRAGGING_HOLE:
            holesActions.endDraggingHole(x, y);
            break;

          case constants.MODE_ROTATING_ITEM:
            itemsActions.endRotatingItem(x, y);
            break;
          case constants.MODE_COPY_PASTE: {
            if (draggingSelection) {
              copyPasteActions.endDraggingCopyPasteSelection(x, y);
            } else if (rotatingSelection) {
              copyPasteActions.endRotatingCopyPasteSelection(x, y);
            } else {
              copyPasteActions.endCopyPasteSelection(x, y);
            }
            break;
          }
          case constants.MODE_RECTANGLE_TOOL:
            rectangleToolActions.endRectangleSelection(x, y);
            break;
        }

        event.stopPropagation();
      },
      [ctrlActive, mode, snapMask, draggingSelection, rotatingSelection]
    );

    return (
      <UncontrolledReactSVGPanZoom
        className={SVG_PLAN_CLASSNAME}
        ref={Viewer2DRef}
        style={{ gridColumn: 2, gridRow: 2 }}
        width={width - rulerSize}
        height={height - rulerSize}
        tool={mode2Tool(mode, alterate)}
        detectAutoPan={mode2DetectAutopan(mode)}
        onMouseDown={!isPendingRequest ? onMouseDown : () => {}}
        onMouseMove={!isPendingRequest ? onMouseMove : () => {}}
        onMouseUp={onMouseUp}
        toolbarProps={toolbarProps}
        miniatureProps={miniatureProps}
      >
        {children}
      </UncontrolledReactSVGPanZoom>
    );
  }
);

function mapStateToProps(state) {
  state = state['react-planner'];
  const { ctrlActive, mode, alterate, snapMask, scene } = state;
  const rectangleToolDrawingSelection = state.rectangleTool?.drawing;
  const rectangleToolSelection = state.rectangleTool.selection;
  const drawingSelection = state.copyPaste.drawing;
  const draggingSelection = state.copyPaste.dragging;
  const rotatingSelection = state.copyPaste.rotating;
  const copyPasteSelection = state.copyPaste.selection;

  const savingAnnotationsKey = constants.REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS;
  const requestSavingAnnotationsStatus = state.requestStatus[savingAnnotationsKey];
  const isPendingRequest = requestSavingAnnotationsStatus?.status === constants.RequestStatusType.PENDING;
  const layerID = scene.selectedLayer;
  const sceneWidth = scene.width;
  const sceneHeight = scene.height;

  return {
    state,
    ctrlActive,
    sceneWidth,
    sceneHeight,
    mode,
    alterate,
    layerID,
    snapMask,
    rectangleToolDrawingSelection,
    drawingSelection,
    draggingSelection,
    rotatingSelection,
    copyPasteSelection,
    rectangleToolSelection,
    isPendingRequest,
  };
}

const mapDispatchToProps = dispatch => {
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(SvgPanZoom);

function extractElementData(node) {
  while (!node.attributes.getNamedItem('data-element-root') && node.tagName !== 'svg') {
    node = node.parentNode;
  }
  if (node.tagName === 'svg') return null;

  return {
    part: node.attributes.getNamedItem('data-part') ? node.attributes.getNamedItem('data-part').value : undefined,
    layer: node.attributes.getNamedItem('data-layer').value,
    prototype: node.attributes.getNamedItem('data-prototype').value,
    selected: node.attributes.getNamedItem('data-selected').value === 'true',
    id: node.attributes.getNamedItem('data-id').value,
  };
}

function mode2Tool(mode, alterate) {
  if (
    alterate &&
    (constants.MODE_WAITING_DRAWING_LINE ||
      constants.MODE_DRAWING_LINE ||
      constants.MODE_DRAWING_HOLE ||
      constants.MODE_DRAWING_ITEM ||
      constants.MODE_DRAGGING_VERTEX ||
      constants.MODE_DRAGGING_HOLE ||
      constants.MODE_DRAGGING_ITEM)
  ) {
    return TOOL_PAN;
  }

  switch (mode) {
    case constants.MODE_2D_PAN:
      return TOOL_PAN;
    case constants.MODE_2D_ZOOM_IN:
      return TOOL_ZOOM_IN;
    case constants.MODE_2D_ZOOM_OUT:
      return TOOL_ZOOM_OUT;
    case constants.MODE_IDLE:
      return TOOL_AUTO;
    default:
      return TOOL_NONE;
  }
}

function mode2DetectAutopan(mode) {
  switch (mode) {
    case constants.MODE_DRAWING_LINE:
    case constants.MODE_DRAGGING_VERTEX:
    case constants.MODE_DRAGGING_HOLE:
    case constants.MODE_DRAGGING_ITEM:
    case constants.MODE_DRAWING_HOLE:
    case constants.MODE_DRAWING_ITEM:
      return true;

    default:
      return false;
  }
}
