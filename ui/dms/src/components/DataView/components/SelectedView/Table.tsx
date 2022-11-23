import React, { useEffect, useState } from 'react';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList as WindowedList } from 'react-window';
import { Icon } from 'archilyse-ui-components';
import cn from 'classnames';
import { ItemIcon, Tags, Truncate } from 'Components';
import {
  formatPrice,
  inView,
  isCustomFolder,
  isCustomFolderAsEntity,
  isEntityFolder,
} from 'Components/DataView/modules';
import { useStore } from 'Components/DataView/hooks';
import { C } from 'Common';
import './table.scss';
import { useWindowSize } from 'Common/hooks';

const { SITES, UNITS, ROOMS, FLOORS, BUILDINGS, TRASH } = C.DMS_VIEWS;

const CLIENTS_TYPE = 'folder-clients';
const TAGS = 'labels';

const SORT_ICON_COLOR = '#8C9294';
const TYPE_ICON_COLOR = '#8A9092';

const insideAClient = pathname => inView([SITES, BUILDINGS, FLOORS, UNITS, ROOMS], pathname);

const TYPE_STYLE = {
  height: '32px',
  width: '32px',
  fontSize: '32px',
  color: TYPE_ICON_COLOR,
  marginLeft: undefined,
};

const ROW_SIZE = 60;
const ASCENDING = 1;
const DESCENDING = -1;

const NAME = 'name';
const CREATED = 'created';
const UPDATED = 'updated';

const DAYS_TO_EXPIRE = 30;

const allowTags = row => ![CLIENTS_TYPE].includes(row.type);
const getColumn = pathname => {
  if (pathname.includes('unit') || pathname.includes('floors')) return [...DMS_COLUMNS, ...DMS_PH_COLUMNS];
  if (pathname.includes('trash')) return [...DMS_COLUMNS, ...DMS_TRASH_COLUMNS];
  if (pathname.includes('sites')) return DMS_SITE_COLUMNS;
  return DMS_COLUMNS;
};

const renderTags = ({ rows = [], row, value, selectedRow = { type: '', id: '' }, onChange }) => {
  if (!allowTags(row)) return null;
  const isSelected = row.type === selectedRow.type && row.id === selectedRow.id;
  const allTags = rows.reduce((accum, row) => [...accum, ...(row.labels || [])], []);
  const suggestions = allTags.filter((option, index) => allTags.indexOf(option) === index);
  return (
    <Tags
      disablePortal={false}
      suggestions={suggestions}
      onChange={(event, value) => onChange({ ...row, labels: value })}
      value={value}
      editable={isSelected}
    />
  );
};

const renderName = ({ row, value }) => {
  return (
    <div className="folder-name-data">
      <div className="folder-type-icon">
        <ItemIcon mimeType={row.type} style={TYPE_STYLE} />
      </div>
      <div className="folder-name">{value}</div>
    </div>
  );
};

const renderExpiryDate = value => {
  const updated = new Date(value);
  const expiry = new Date(updated.setDate(updated.getDate() + DAYS_TO_EXPIRE));
  return expiry.toLocaleString();
};

const formatPHValue = value => {
  if (value === 0) return '-';
  if (isNaN(value)) return '';
  return value;
};

const formatPHPrice = value => {
  if (typeof value === 'number' && value !== 0) {
    return formatPrice(value);
  }
  return formatPHValue(value);
};

const formatPHFactor = value => {
  if (!isNaN(value) && typeof value === 'number' && value !== 0) {
    if (value < 0) return (value * 100).toFixed(2) + '%';
    return '+' + (value * 100).toFixed(2) + '%';
  }
  return formatPHValue(value);
};

const STYLE = {
  fontSize: '20px',
  marginLeft: '5px',
  color: SORT_ICON_COLOR,
};

const getSortArrow = (column, sortedBy, sortOrder) => {
  const isOrdered = column.field === sortedBy;
  if (!isOrdered) {
    return null;
  }
  return sortOrder === DESCENDING ? <Icon style={STYLE}>south</Icon> : <Icon style={STYLE}>north</Icon>;
};

const DMS_COLUMNS = [
  {
    headerName: 'Name',
    field: 'name',
    className: 'name',
    renderer: renderName,
  },
  {
    headerName: 'Tags',
    className: 'tags',
    field: TAGS,
    renderer: renderTags,
  },
];

const DMS_SITE_COLUMNS = [
  {
    headerName: 'Name',
    field: 'name',
    className: 'name',
    renderer: renderName,
  },
  {
    headerName: 'Client Site Id',
    field: 'clientSiteId',
    className: 'clientSiteId',
    renderer: params => (
      <Truncate maxWidth={params.maxWidth} maxHeight={params.maxHeight} type="middle">
        {params.value}
      </Truncate>
    ),
  },
  {
    headerName: 'Tags',
    className: 'tags',
    field: TAGS,
    renderer: renderTags,
  },
];

const DMS_PH_COLUMNS = [
  {
    headerName: 'Yearly Gross Rent',
    className: 'phPrice',
    field: 'phPrice',
    renderer: params => formatPHPrice(params.value),
  },
  {
    headerName: 'Layout Premium',
    className: 'phFactor',
    field: 'phFactor',
    renderer: params => formatPHFactor(params.value),
  },
];

const DMS_TRASH_COLUMNS = [
  {
    headerName: 'Expiry Date',
    className: 'expiryDate',
    field: 'updated',
    renderer: params => renderExpiryDate(params.value),
  },
];

const Header = ({ width, sortRowsBy, sortOrder, sortedBy, nameRef, columns }) => {
  return (
    <div className="thead" style={{ width }}>
      <div className="tr">
        {columns.map(column => (
          <div
            ref={column.field === 'name' ? nameRef : null}
            className={`th ${column.className || ''}`}
            key={column.field}
            data-testid={column.field}
            onClick={() => sortRowsBy(column.field)}
          >
            <span className="column-header-name">{column.headerName}</span>
            {getSortArrow(column, sortedBy, sortOrder)}
          </div>
        ))}
      </div>
    </div>
  );
};

const Cell = ({ rows, row, column, onClickRow, selectedRow, onChangeRow, headerNameRef }) => {
  useWindowSize();
  const value = row[column.field];
  const onClick = column.field !== TAGS ? onClickRow : () => {};
  const maxWidth = headerNameRef?.offsetWidth;
  const maxHeight = headerNameRef?.offsetHeight;
  const renderParams = { rows, row, value, selectedRow, onChange: onChangeRow, maxWidth, maxHeight };

  return (
    <div onClick={() => onClick(row)} className={`td ${column.className || ''}`}>
      {column.renderer ? column.renderer(renderParams) : String(value)}
    </div>
  );
};

const Row = ({ index, style, data }) => {
  const {
    columns,
    rows,
    itemInClipboard,
    hoveredItem,
    selectedRow,
    onClickRow,
    onChangeRow,
    handleMouseEnter,
    handleMouseLeave,
    onContextMenuRow,
    headerNameRef,
  } = data;

  const row = rows[index];

  const isHovered = hoveredItem && row.id === hoveredItem.id && row.type === hoveredItem.type;
  const isCut = row.id === itemInClipboard?.id && row.type === itemInClipboard?.type;

  return (
    <div
      style={style}
      key={`${row.type} - ${row.id}`}
      onMouseEnter={handleMouseEnter(row)}
      onMouseLeave={handleMouseLeave(row)}
      onContextMenu={event => onContextMenuRow(event, row)}
      className={cn('tr', { hover: isHovered, 'item-cut': isCut })}
    >
      {columns.map((column, index) => (
        <Cell
          key={`td - ${index} - ${column.field}`}
          column={column}
          rows={rows}
          row={row}
          onClickRow={onClickRow}
          selectedRow={selectedRow}
          onChangeRow={onChangeRow}
          headerNameRef={headerNameRef}
        />
      ))}
    </div>
  );
};
const Body = ({
  columns,
  onItemsRendered,
  height,
  visibleItems,
  onInitialRender,
  rows,
  onClickRow,
  onContextMenuRow,
  onChangeRow,
  onMouseEnter,
  onMouseLeave,
  hoveredItem,
  itemInClipboard,
  pathname,
  sortedBy,
  sortOrder,
  width,
  headerNameRef,
}) => {
  const [selectedRow, setSelectedRow] = useState<any>();
  const handleMouseEnter = row => () => {
    setSelectedRow(row);
    onMouseEnter(row);
  };

  useEffect(() => {
    if (insideAClient(pathname) && (!visibleItems || !visibleItems.length) && rows?.length > 0) {
      onInitialRender(rows, height);
    }
  }, [rows, height, pathname, visibleItems]);

  useEffect(() => {
    if (visibleItems?.length > 0) {
      onInitialRender(rows, height);
    }
  }, [sortedBy, sortOrder]);

  const handleMouseLeave = row => () => {
    setSelectedRow(undefined);
    onMouseLeave(row);
  };
  const listHeight = height - ROW_SIZE; //Otherwise the last row is not taken into account and not shown.
  return (
    <div className="tbody" style={{ width }}>
      <WindowedList
        height={listHeight}
        itemCount={rows.length}
        itemSize={ROW_SIZE}
        onItemsRendered={onItemsRendered}
        itemData={{
          columns,
          rows,
          itemInClipboard,
          hoveredItem,
          selectedRow,
          onClickRow,
          onChangeRow,
          handleMouseEnter,
          handleMouseLeave,
          onContextMenuRow,
          headerNameRef,
        }}
        width={width}
      >
        {Row}
      </WindowedList>
    </div>
  );
};

const sortRows = (rows, sortOrder, sortedBy) => {
  return rows.slice().sort((rowA, rowB) => {
    if (sortOrder === ASCENDING) {
      return String(rowA[sortedBy]).localeCompare(rowB[sortedBy], undefined, { numeric: true });
    }
    return String(rowB[sortedBy]).localeCompare(rowA[sortedBy], undefined, { numeric: true });
  });
};

const Table = ({
  data = [],
  itemInClipboard,
  onClickFolder,
  onClickCustomFolder,
  onClickFile,
  onChangeTags,
  onContextMenu,
  onMouseEnter,
  onMouseLeave,
  pathname,
}) => {
  const [sortOrder, setSortOrder] = useState<number>(ASCENDING);
  const [sortedBy, setSortedBy] = useState<string>(CREATED);
  const hoveredItem = useStore(state => state.hoveredItem);
  const visibleItems = useStore(state => state.visibleItems);
  const setVisibleItems = useStore(state => state.setVisibleItems);

  const [headerNameRef, setHeaderNameRef] = useState<HTMLDivElement>();

  useEffect(() => {
    if (inView([FLOORS], pathname)) {
      setSortedBy(NAME);
    }
    if (inView([TRASH], pathname)) {
      setSortedBy(UPDATED);
    }
  }, [pathname]);

  const sortRowsBy = field => {
    setSortedBy(field);
    sortOrder === ASCENDING ? setSortOrder(DESCENDING) : setSortOrder(ASCENDING);
  };

  const onClickRow = row => {
    if (isCustomFolder(row) || isCustomFolderAsEntity(row)) return onClickCustomFolder(row);
    if (isEntityFolder(row)) return onClickFolder(row);
    return onClickFile(row);
  };

  const onContextMenuRow = (event, row) => {
    if (isCustomFolder(row) || !isEntityFolder(row)) {
      return onContextMenu(event, row);
    }
    return () => {};
  };

  const onChangeRow = newRow => {
    onChangeTags(newRow);
  };

  const onInitialRender = (rows, height) => {
    const nrOfInitialItems = Math.floor(height / ROW_SIZE);
    setVisibleItems(rows.slice(0, nrOfInitialItems + 1));
  };

  const onItemsRendered = ({ visibleStartIndex, visibleStopIndex }) => {
    const newItems = rows.slice(visibleStartIndex, visibleStopIndex + 1);
    setVisibleItems(newItems);
  };

  const rows = sortOrder ? sortRows(data, sortOrder, sortedBy) : data.slice();
  const columns = getColumn(pathname);
  return (
    <div className="dms-table" data-testid="dms-table" onContextMenu={onContextMenu}>
      <AutoSizer>
        {({ width, height }) => (
          <div className="table">
            <Header
              columns={columns}
              width={width}
              sortRowsBy={sortRowsBy}
              sortOrder={sortOrder}
              sortedBy={sortedBy}
              nameRef={setHeaderNameRef}
            />
            <Body
              columns={columns}
              pathname={pathname}
              height={height}
              width={width}
              itemInClipboard={itemInClipboard}
              rows={rows}
              onClickRow={onClickRow}
              onChangeRow={onChangeRow}
              onContextMenuRow={onContextMenuRow}
              onMouseEnter={onMouseEnter}
              onMouseLeave={onMouseLeave}
              hoveredItem={hoveredItem}
              onItemsRendered={onItemsRendered}
              visibleItems={visibleItems}
              onInitialRender={onInitialRender}
              sortedBy={sortedBy}
              sortOrder={sortOrder}
              headerNameRef={headerNameRef}
            />
          </div>
        )}
      </AutoSizer>
    </div>
  );
};

export default Table;
