import './admin.scss';

import { Breadcrumb, Search } from 'Components';
import { capitalize, Icon, ProviderStorage } from 'archilyse-ui-components';
import React, { useEffect, useState } from 'react';
import { useHierarchy, useRouter } from 'Common/hooks';

import { C } from 'Common';
import { Fab } from '@material-ui/core/';
import Table from 'Components/Table';

const { TABLE_SEARCH } = C.STORAGE;

const filterData = (rows = [], columns, filter) => {
  if (!filter) return rows;
  const headers = columns.map(c => c.field);
  return rows?.filter(row => {
    return Object.entries(row).some(([key, cell = '']) => {
      const visible = headers.includes(key);
      return visible && String(cell).toLowerCase().includes(filter);
    });
  });
};

const Title = ({ pathname }) => (
  <div className="table-title">
    <h2>{capitalize(pathname.replace('/', ''))}</h2>
  </div>
);

type TablePropsType = {
  id: string;
  rows: any[];
  columns: any[];
  allowCreation?: boolean;
  onExpand?: Function;
  parentFilter?: string;
  className?: '';
  onTableReady?: any;
  rowHeight?: number;
};
const AdminView = (props: TablePropsType) => {
  const {
    id,
    rows,
    columns,
    allowCreation = false,
    parentFilter = '',
    rowHeight = undefined,
    className = '',
    onTableReady = undefined,
  } = props;
  const { pathname, history, fullPath } = useRouter();
  const [filter, setFilter] = useState(undefined);
  const hierarchy = useHierarchy();

  const onCreateClick = () => {
    const context = pathname.slice(0, -1);
    history.push(`${context}/new?${parentFilter}`);
  };

  const onFilterChange = value => {
    const filter = value.toLowerCase();
    setFilter(filter || '');
    ProviderStorage.set(TABLE_SEARCH(fullPath), filter);
  };

  useEffect(() => {
    const savedFilter = ProviderStorage.get(TABLE_SEARCH(fullPath));
    if (savedFilter) {
      setFilter(savedFilter);
    } else {
      setFilter('');
    }
  }, [fullPath]);

  const filteredRows = filterData(rows, columns, filter);
  return (
    <div className="admin-view">
      <div className="data-header">
        <div className="controls">
          <div className="breadcrumb">
            <Breadcrumb hierarchy={hierarchy} />
          </div>
          {filter !== null && filter !== undefined && (
            <Search
              initialValue={filter}
              onFilterChange={onFilterChange}
              delay={(rows || []).length > 100 ? C.DELAY_FILTER_MS : 0}
            />
          )}
        </div>
      </div>
      <Title pathname={pathname} />
      <div className="table-top">
        {allowCreation && (
          <div className="add-icon" onClick={onCreateClick}>
            <Fab color="inherit" aria-label="add">
              <Icon style={{ color: 'inherit', marginLeft: undefined }}>add</Icon>
            </Fab>
          </div>
        )}
      </div>
      <Table
        id={id}
        columns={columns}
        rows={filteredRows}
        pagination={true}
        onTableReady={onTableReady}
        rowHeight={rowHeight}
        className={className}
      />
    </div>
  );
};

export default AdminView;
