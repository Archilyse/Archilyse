import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import If from '../../utils/react-if';
import { ProviderHash } from '../../providers';
import { COLORS, MODE_COPY_PASTE } from '../../constants';
import getSelectedAnnotationsSize from '../../utils/get-selected-annotations-size';

const STYLE_CIRCLE = {
  fill: COLORS.SELECTED_ELEMENT,
  stroke: COLORS.SELECTED_ELEMENT,
  cursor: 'ew-resize',
};

const STYLE_CIRCLE2 = {
  fill: 'none',
  stroke: COLORS.SELECTED_ELEMENT,
  cursor: 'ew-resize',
};

const ARROW_STYLE = {
  stroke: COLORS.SELECTED_ELEMENT,
  strokeWidth: '2px',
  fill: COLORS.SELECTED_ELEMENT,
};

const ARROW_WIDTH = 40;
const ARROW_HEIGHT = 150;

const OrientationArrow = () => (
  <>
    <line key="2" x1={0} x2={0} y1={ARROW_HEIGHT} y2={ARROW_HEIGHT + 30} style={ARROW_STYLE} />
    <line key="3" x1={0.25 * ARROW_WIDTH} x2={0} y1={ARROW_HEIGHT + 15} y2={ARROW_HEIGHT + 30} style={ARROW_STYLE} />
    <line key="4" x1={0} x2={-0.25 * ARROW_WIDTH} y1={ARROW_HEIGHT + 30} y2={ARROW_HEIGHT + 15} style={ARROW_STYLE} />
  </>
);

const Item = ({ layer, item, scene, catalog, mode, multipleAnnotationsSelected }) => {
  const { x, y, rotation } = item;

  const renderedItem = catalog.getElement(item.type).render2D(item, layer, scene);
  const commonDataAttributes = {
    'data-id': item.id,
    'data-prototype': item.prototype,
    'data-selected': item.selected,
    'data-layer': layer.id,
  };

  return (
    <g
      data-element-root
      style={item.selected ? { cursor: 'move' } : {}}
      transform={`translate(${x},${y}) rotate(${rotation})`}
      data-testid={`viewer-item-${item.id}`}
      {...commonDataAttributes}
    >
      {renderedItem}
      <If condition={item.selected && !multipleAnnotationsSelected}>
        <g data-element-root data-part="rotation-anchor" {...commonDataAttributes}>
          {mode !== MODE_COPY_PASTE && (
            <>
              <OrientationArrow />
              <circle cx="0" cy="150" r="10" style={STYLE_CIRCLE} />
            </>
          )}
          <circle cx="0" cy="0" r="150" style={STYLE_CIRCLE2} />
        </g>
      </If>
    </g>
  );
};

Item.propTypes = {
  item: PropTypes.object.isRequired,
  layer: PropTypes.object.isRequired,
  scene: PropTypes.object.isRequired,
  catalog: PropTypes.object.isRequired,
};

export const areEqual = (prevProps, nextProps) => {
  // Check if item has changed
  if (prevProps.item !== nextProps.item) {
    return false;
  }

  // Check if multiple annotations are selected
  if (prevProps.multipleAnnotationsSelected !== nextProps.multipleAnnotationsSelected) {
    return false;
  }

  // Allow re-rerendering item if it's selected or unselected
  if (prevProps.item.selected !== nextProps.item.selected) {
    return false;
  }

  // Allow re-rendering item if it's moving (ie. dragging)
  const differentXcoords = prevProps.item.x !== nextProps.item.x;
  const differentYcoords = prevProps.item.y !== nextProps.item.y;
  if (differentXcoords || differentYcoords) {
    return false;
  }

  // Allow re-rendering item if properties are being changed
  const differentWidth = prevProps.item.properties.width.value !== nextProps.item.properties.width.value;
  const differentLength = prevProps.item.properties.length.value !== nextProps.item.properties.length.value;
  if (differentWidth || differentLength) {
    return false;
  }

  // Allow re-rendering item if rotation is being changed
  const differentRotation = prevProps.item.rotation !== nextProps.item.rotation;
  if (differentRotation) {
    return false;
  }

  // Allow re-rendering item if type is being changed
  const differentType = prevProps.item.type !== nextProps.item.type;
  if (differentType) {
    return false;
  }

  return true;
};

const MemoizedItem = React.memo(Item, areEqual);

function mapStateToProps(state) {
  state = state['react-planner'];
  const selectedAnnotationsSize = getSelectedAnnotationsSize(state);
  const multipleAnnotationsSelected = selectedAnnotationsSize > 1;
  return {
    multipleAnnotationsSelected,
  };
}

export default connect(mapStateToProps)(MemoizedItem);
