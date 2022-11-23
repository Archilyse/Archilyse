import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import ToolbarButton from '../toolbar-button/export';
import { COLORS, PrototypesEnum } from '../../constants';
import * as SharedStyle from '../../shared-style';

import { objectsMap } from '../../utils/objects-utils';
import { holesActions, itemsActions, linesActions } from '../../actions/export';
import getAnnotationsSizeByPrototype from '../../utils/get-annotations-size-by-prototype';

const ASIDE_STYLE = {
  backgroundColor: SharedStyle.PRIMARY_COLOR.main,
};

const GRID_STYLE = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gridTemplateAreas: 'auto',
  columnGap: '10px',
  rowGap: '20px',
};

const HR_STYLE = { width: '100%' };

type CatalogElement = {
  name: string;
  prototype: string;
  info: {
    title: string;
    toolbarIcon?: JSX.Element;
    visibility?: {
      catalog?: boolean;
      layerElementsVisible?: boolean; // @TODO: Deprecated, remove
    };
  };
  properties: any;
};

// We had to add hover and click here so the user can click on text name and not only in the
// icon. Ideally we could put <small> text inside toolbarbutton, but this required a lot of style changes
const CatalogElement = ({ element, active, onClick, disabled }) => {
  const [hover, setHover] = useState(false);
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        cursor: disabled ? 'default' : 'pointer',
        color: hover ? COLORS.TOOLBAR_ACTIVE_ICON : 'white',
        background: 'none',
        border: 'none',
        opacity: disabled ? '0.6' : '1',
      }}
      onMouseOver={() => !disabled && setHover(true)}
      onMouseOut={() => !disabled && setHover(false)}
      onClick={() => (disabled ? () => {} : onClick())}
    >
      <ToolbarButton key={element.name} active={active || hover}>
        {element.info.toolbarIcon}
      </ToolbarButton>
      <small>{element.info.title}</small>
    </div>
  );
};

const getCatalogElements = (elements: Record<string, CatalogElement>) => {
  const catalogElements: CatalogElement[] = Object.values(elements).filter(
    e => e.info.toolbarIcon && Boolean(!e.info.visibility || e.info?.visibility?.catalog)
  );

  // All elements are sorted alphabetically but the lines, that have a special order
  const lines: CatalogElement[] = catalogElements.filter(e => e.prototype === 'lines').reverse();
  const holes: CatalogElement[] = catalogElements.filter(e => e.prototype === 'holes');
  const items: CatalogElement[] = catalogElements.filter(e => e.prototype === 'items');
  return { lines, holes, items };
};

const CatalogToolbar = React.memo(
  ({
    width: toolbarWidth,
    height,
    catalogElements,
    drawingSupportType,

    selectedLines,
    selectedHoles,
    selectedItems,
    linesSize,
    holesSize,
    itemsSize,
    onlyOnePrototypeSelected,

    holesActions,
    itemsActions,
    linesActions,
  }: any): JSX.Element => {
    const { lines, holes, items } = useMemo(() => getCatalogElements(catalogElements), [catalogElements]);

    const onClickLine = element => linesActions.selectToolDrawingLine(element.name);
    const onClickHole = element => holesActions.selectToolDrawingHole(element.name);
    const onClickItem = element => itemsActions.selectToolDrawingItem(element.name);

    const isElementSelected = element => {
      return drawingSupportType === element.name;
    };

    // this funtion gets called only when an annotation is selected
    const handleElementClick = elem => {
      const elementType = elem.name;
      const { prototype } = elem;
      const changeElement = {
        [PrototypesEnum.LINES]: () => {
          const selectedLineIds = selectedLines;
          linesActions.changeLinesType(selectedLineIds, elementType);
        },
        [PrototypesEnum.ITEMS]: () => {
          const selectedItemsIds = selectedItems;
          itemsActions.changeItemsType(selectedItemsIds, elementType);
        },
        [PrototypesEnum.HOLES]: () => {
          const selectedHoleIds = selectedHoles;
          holesActions.changeHolesType(selectedHoleIds, elementType);
        },
      };

      changeElement[prototype]();
    };

    return (
      <aside
        style={{
          ...ASIDE_STYLE,
          maxWidth: toolbarWidth + 220,
          height,
          overflowY: 'auto',
          position: 'absolute',
          left: toolbarWidth,
          zIndex: 500,
        }}
        id="catalog-toolbar"
        data-testid="catalog-toolbar"
        className="toolbar"
      >
        <div style={{ height: '100%', padding: '20px' }}>
          <div style={GRID_STYLE}>
            {lines.map(e => (
              <CatalogElement
                key={e.name}
                element={e}
                disabled={onlyOnePrototypeSelected && linesSize === 0}
                active={onlyOnePrototypeSelected && linesSize > 0 ? false : isElementSelected(e)}
                onClick={() => (onlyOnePrototypeSelected ? handleElementClick(e) : onClickLine(e))}
              />
            ))}
          </div>
          <hr style={HR_STYLE}></hr>
          <div style={GRID_STYLE}>
            {holes.map(e => (
              <CatalogElement
                key={e.name}
                element={e}
                disabled={onlyOnePrototypeSelected && holesSize === 0}
                active={onlyOnePrototypeSelected && holesSize > 0 ? false : isElementSelected(e)}
                onClick={() => (onlyOnePrototypeSelected ? handleElementClick(e) : onClickHole(e))}
              />
            ))}
          </div>
          <hr style={HR_STYLE}></hr>
          <div style={GRID_STYLE}>
            {items.map(e => (
              <CatalogElement
                key={e.name}
                element={e}
                disabled={onlyOnePrototypeSelected && itemsSize === 0}
                active={onlyOnePrototypeSelected && itemsSize > 0 ? false : isElementSelected(e)}
                onClick={() => (onlyOnePrototypeSelected ? handleElementClick(e) : onClickItem(e))}
              />
            ))}
          </div>
        </div>
      </aside>
    );
  }
);

export const areEqual = (prevProps, nextProps) => {
  // Check if drawingSupport.type has changed
  if (prevProps.state.drawingSupport.type !== nextProps.state.drawingSupport.type) {
    return false;
  }

  return true;
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const drawingSupportType = state.drawingSupport.type;
  const catalogElements = state.catalog.elements;
  const {
    selectedLines,
    linesSize,
    selectedHoles,
    holesSize,
    selectedItems,
    itemsSize,
    onlyOnePrototypeSelected,
  } = getAnnotationsSizeByPrototype({ state });
  return {
    drawingSupportType,
    catalogElements,
    selectedLines,
    linesSize,
    selectedHoles,
    holesSize,
    selectedItems,
    itemsSize,
    onlyOnePrototypeSelected,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { holesActions, itemsActions, linesActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(CatalogToolbar);
