import { AgGridReact } from 'ag-grid-react';
import React, { useEffect, useState } from 'react';
import 'ag-grid-community/dist/styles/ag-grid.css';
import 'ag-grid-community/dist/styles/ag-theme-material.css';
import './table.scss';

let isTableReady;
const WAIT_FOR_CUSTOM_RENDERS = 1000; // Ag-grid fires `ready` event before custom renders are rendered, so we need to wait
const DEFAULT_ROW_HEIGHT = 48;

const onGridReady = (params, rowHeight, onTableReady) => {
  params.api;
  params.columnApi;
  params.api.sizeColumnsToFit();
  window.addEventListener('resize', () => {
    setTimeout(() => {
      params.api.sizeColumnsToFit();
    });
  });
  isTableReady = Boolean(params.api);
  if (onTableReady) onTableReady(params);
};

const Table = ({
  id,
  columns,
  rows,
  rowHeight = DEFAULT_ROW_HEIGHT,
  pagination = false,
  onTableReady = params => {},
  className = '',
}) => {
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  //Use effect to ensure component is mounted and we expect to table ready
  useEffect(() => {
    if (isTableReady) {
      setTimeout(() => setIsDataLoaded(true), WAIT_FOR_CUSTOM_RENDERS);
    }
  }, [isTableReady]);

  return (
    <div id={id} className={`table ag-theme-material ${className}`} data-testid={isDataLoaded ? 'ag-grid-table' : ''}>
      <AgGridReact
        enableCellTextSelection
        onGridReady={params => onGridReady(params, rowHeight, onTableReady)}
        columnDefs={columns}
        pagination={pagination}
        paginationAutoPageSize={true}
        rowData={rows}
        rowHeight={rowHeight}
        rowSelection={'single'}
        rowClass={'row'}
        suppressColumnVirtualisation={true}
      ></AgGridReact>
    </div>
  );
};

export default Table;
