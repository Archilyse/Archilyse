import React, { useEffect, useState } from 'react';
import { EditableProps, Icon, INPUT_TYPES } from 'archilyse-ui-components';
import './editableTable.scss';
import { Tooltip } from '@material-ui/core';
import EditableCell, { EditableCellProps } from './EditableCell';
import EditableTableUtils from './EditableTableUtils';

export type ColumnType = {
  header: string;
  field: string;
  editable?: boolean;
  editableHeader?: boolean;
  type?: INPUT_TYPES;
};

export type RowType = { [key: string]: any };

export type ChangedTableType = { rows: RowType[]; columns: ColumnType[] };

type ColumnOptionType = {
  min?: number;
  max?: number;
  base?: ColumnType[];
};

export type RowOptionType = Pick<EditableCellProps, 'placeholder' | 'renderTitle'> &
  Pick<EditableProps, 'type' | 'inputProps' | 'options' | 'dropdownProps'>;

interface Props {
  columnsOptions: ColumnOptionType;
  fixedColumns?: ColumnType[];
  fixedRows?: RowType[];
  onChange: (table: ChangedTableType) => void;
  rowsOptions?: RowOptionType[];
  createNewByDefault?: boolean;
}

const initialColumnsOptions: ColumnOptionType = {
  min: 1,
  max: null,
  base: null,
};

const EditableTable = ({
  onChange,
  fixedColumns = [],
  fixedRows,
  columnsOptions = initialColumnsOptions,
  rowsOptions = [],
  createNewByDefault = true,
}: Props): JSX.Element => {
  const [changedColumns, setChangedColumns] = useState<ColumnType[]>(() =>
    createNewByDefault ? EditableTableUtils.addNewColumn([]) : []
  );
  const [changedRows, setChangedRows] = useState<RowType[]>([]);

  const handleAddColumn = () => {
    const newColumns = EditableTableUtils.addNewColumn(changedColumns);
    setChangedColumns(newColumns);

    onChange({ columns: newColumns, rows: changedRows });
  };

  const handleRemoveColumn = field => () => {
    const [updatedColumns, updatedRows] = EditableTableUtils.removeColumn(changedColumns, changedRows, field);
    setChangedColumns(updatedColumns);
    setChangedRows(updatedRows);

    onChange({ columns: updatedColumns, rows: updatedRows });
  };

  const handleHeaderChange = field => (newValue: string) => {
    const newColumns = EditableTableUtils.changeColumns(changedColumns, field, newValue);
    setChangedColumns(newColumns);

    onChange({ columns: newColumns, rows: changedRows });
  };

  const handleRowChange = (rowIndex, field) => (newValue: string) => {
    if (newValue === '') return;

    const newRows = EditableTableUtils.changeRows(changedRows, rowIndex, field, newValue);
    setChangedRows(newRows);
  };

  const handleMultipleRowChange = (changedIndex, field) => (newValues: string[]) => {
    const newRows = EditableTableUtils.changeMultipleRows(changedRows, changedIndex, field, newValues);
    setChangedRows(newRows);
  };

  useEffect(() => {
    if (fixedRows) setChangedRows(fixedRows);
  }, [fixedRows]);

  useEffect(() => {
    if (fixedColumns) {
      if (Number.isInteger(columnsOptions.max) && fixedColumns.length >= columnsOptions.max) {
        setChangedColumns(fixedColumns);
      } else {
        setChangedColumns(EditableTableUtils.addNewColumn(fixedColumns));
      }
    }
  }, [fixedColumns, columnsOptions.max]);

  useEffect(() => {
    onChange({ columns: changedColumns, rows: changedRows });
  }, [changedColumns, changedRows]);

  const renderColumn = (column: ColumnType) => {
    const value = column.header;
    if (column.editableHeader) {
      return (
        <EditableCell
          key={column.field}
          onSave={handleHeaderChange(column.field)}
          onRemove={changedColumns.length > columnsOptions.min && handleRemoveColumn(column.field)}
          value={value}
          component={'th'}
        />
      );
    }

    return <th key={column.field}>{value}</th>;
  };

  const renderRow = (row: RowType, index: number) => (column: ColumnType) => {
    const value = row[column.field];
    const rowOption = rowsOptions[index];
    if (column.editable) {
      return (
        <EditableCell
          key={column.field}
          onSave={handleRowChange(index, column.field)}
          onMultipleCellsChange={handleMultipleRowChange(index, column.field)}
          value={value}
          type={column.type}
          {...rowOption}
        />
      );
    }

    return <td key={column.field}>{value}</td>;
  };

  const canAdd = !Number.isInteger(columnsOptions.max) || changedColumns.length < columnsOptions.max;

  return (
    <div className="editable-table-container">
      <table>
        <thead className="editable-table-header">
          <tr>
            {changedColumns.map(renderColumn)}
            {canAdd && (
              <th>
                <Tooltip title="Add new column">
                  <button className="editable-table-add-column" onClick={handleAddColumn}>
                    <Icon style={{ fontSize: 25, width: 25, height: 25 }}>add</Icon>
                  </button>
                </Tooltip>
              </th>
            )}
          </tr>
        </thead>
        <tbody className="editable-table-body">
          {changedRows.map((row, index) => (
            <tr key={index} className="row">
              {changedColumns.map(renderRow(row, index))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EditableTable;
