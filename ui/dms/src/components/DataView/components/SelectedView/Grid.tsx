import React, { useEffect } from 'react';
import cn from 'classnames';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeGrid as WindowedGrid } from 'react-window';
import { inView, isCustomFolder, isCustomFolderAsEntity, isEntityFolder } from 'Components/DataView/modules';
import { ItemIcon, Truncate } from 'Components';
import { C } from 'Common';
import { useStore } from '../../hooks';
import './grid.scss';

const { SITES, UNITS, ROOMS, FLOORS, BUILDINGS } = C.DMS_VIEWS;

const GRID_ICON_STYLE = {
  width: '50px',
  height: '50px',
  fontSize: '50px',
  marginLeft: 0,
};

const COL_WIDTH = 180;
const ROW_HEIGHT = 165;

const insideAClient = pathname => inView([SITES, BUILDINGS, FLOORS, UNITS, ROOMS], pathname);

const toMatrix = (array, columns) => {
  const matrix = [];
  for (let index = 0, column = -1; index < array.length; index++) {
    if (index % columns === 0) {
      column++;
      matrix[column] = [];
    }
    matrix[column].push(array[index]);
  }
  return matrix;
};

const flattenArray = matrix => [].concat(...matrix);

const Item = ({ columnIndex, rowIndex, style, data }) => {
  const { gridData, itemInClipboard, onClickItem, hoveredItem, onContextMenu, onMouseEnter, onMouseLeave } = data;

  const item = gridData[rowIndex] && gridData[rowIndex][columnIndex];
  if (!item) return null;

  const onFileContextMenu = !isEntityFolder(item) ? onContextMenu : () => {};
  const isHovered = hoveredItem && item.id === hoveredItem.id && item.type === hoveredItem.type;
  const isCut = item.id === itemInClipboard?.id && item.type === itemInClipboard?.type;
  return (
    <div
      style={style}
      key={`${item.type} - ${item.id}`}
      className="grid-item-container"
      onMouseEnter={() => onMouseEnter(item)}
      onMouseLeave={() => onMouseLeave(item)}
    >
      <div
        style={{ height: '80%', width: '80%' }}
        className={cn(isEntityFolder(item) || isCustomFolder(item) ? 'folder' : 'file', {
          hover: isHovered,
          'item-cut': isCut,
        })}
        onClick={() => onClickItem(item)}
        onContextMenu={event => onFileContextMenu(event, item)}
      >
        <ItemIcon mimeType={item.type} style={GRID_ICON_STYLE} />
        {isHovered ? <p>{item.name}</p> : <Truncate maxWidth={COL_WIDTH}>{item.name}</Truncate>}
      </div>
    </div>
  );
};

const ContainerGrid = ({ nrOfRows, nrOfColumns, visibleItems, pathname, onInitialRender, gridData, children }) => {
  useEffect(() => {
    if (insideAClient(pathname) && (!visibleItems || !visibleItems.length) && gridData?.length > 0) {
      onInitialRender(gridData, nrOfRows, nrOfColumns);
    }
  }, [nrOfRows, nrOfColumns, visibleItems, gridData, pathname]);
  return <>{children}</>;
};

const Grid = ({
  data = [],
  pathname,
  itemInClipboard,
  onClickFolder,
  onClickCustomFolder,
  onClickFile,
  onContextMenu,
  onMouseEnter,
  onMouseLeave,
}) => {
  const hoveredItem = useStore(state => state.hoveredItem);
  const visibleItems = useStore(state => state.visibleItems);
  const setVisibleItems = useStore(state => state.setVisibleItems);

  const onClickItem = item => {
    if (isCustomFolder(item) || isCustomFolderAsEntity(item)) {
      return onClickCustomFolder(item);
    }
    if (isEntityFolder(item)) {
      return onClickFolder(item);
    }
    return onClickFile(item);
  };

  const onInitialRender = (gridData, nrOfRows, nrOfColumns) => {
    const initialSubset = gridData.slice(0, nrOfRows + 1).slice(0, nrOfColumns + 1);
    setVisibleItems(flattenArray(initialSubset));
  };

  const onItemsRendered = (
    { visibleColumnStartIndex, visibleColumnStopIndex, visibleRowStartIndex, visibleRowStopIndex },
    gridData
  ) => {
    const subsetMatrix = gridData
      .slice(visibleRowStartIndex, visibleRowStopIndex + 1)
      .slice(visibleColumnStartIndex, visibleColumnStopIndex + 1);
    const newItems = flattenArray(subsetMatrix);
    setVisibleItems(newItems);
  };

  return (
    <div className="grid" data-testid="dms-grid" onContextMenu={onContextMenu}>
      <AutoSizer>
        {({ width, height }) => {
          const nrOfColumns = Math.floor(width / COL_WIDTH);
          const nrOfRows = Math.floor(height / ROW_HEIGHT);
          const gridData = toMatrix(data || [], nrOfColumns);
          return (
            <ContainerGrid
              pathname={pathname}
              nrOfColumns={nrOfColumns}
              nrOfRows={nrOfRows}
              gridData={gridData}
              visibleItems={visibleItems}
              onInitialRender={onInitialRender}
            >
              <WindowedGrid
                style={{ overflowX: 'hidden' }}
                columnCount={nrOfColumns}
                columnWidth={COL_WIDTH}
                height={height}
                rowCount={gridData.length}
                rowHeight={ROW_HEIGHT}
                width={width}
                onItemsRendered={indexes => onItemsRendered(indexes, gridData)}
                itemData={{
                  gridData,
                  itemInClipboard,
                  onClickItem,
                  hoveredItem,
                  onContextMenu,
                  onMouseEnter,
                  onMouseLeave,
                }}
              >
                {Item}
              </WindowedGrid>
            </ContainerGrid>
          );
        }}
      </AutoSizer>
    </div>
  );
};

export default Grid;
