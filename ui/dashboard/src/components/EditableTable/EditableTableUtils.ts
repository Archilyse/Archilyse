import { ColumnType, RowType } from './EditableTable';

const DEFAULT_COLUMN_NAME = 'Custom name';

let customColumnsNumber = 0;

class EditableTableUtils {
  static addNewColumn = (columns: ColumnType[]): ColumnType[] => {
    customColumnsNumber += 1;
    const name = EditableTableUtils.generateName(customColumnsNumber);
    const field = EditableTableUtils._toSnakeCase(`${DEFAULT_COLUMN_NAME} ${customColumnsNumber}`);

    const newColumn: ColumnType = {
      header: name,
      field,
      editable: true,
      editableHeader: true,
    };

    return [...columns, newColumn];
  };

  static removeColumn = (columns: ColumnType[], rows: RowType[], field: string): [ColumnType[], RowType[]] => {
    const newColumns = columns.filter(col => col.field !== field);
    const newRows = rows.map(({ [field]: _, ...rest }) => rest);

    return [newColumns, newRows];
  };

  static changeColumns = (columns: ColumnType[], changedField: string, newValue: string): ColumnType[] => {
    const newColumns = columns.map(
      (column): ColumnType => {
        if (column.field === changedField) {
          const value = newValue || EditableTableUtils.generateName(columns.length);
          return { ...column, header: value };
        }

        return column;
      }
    );

    return newColumns;
  };

  static changeRows = (rows: RowType[], changedIndex: number, key: string, newValue: any): RowType[] => {
    const newRows = rows.map((row, index) => {
      if (index === changedIndex) {
        return { ...row, [key]: newValue };
      }

      return row;
    });

    return newRows;
  };

  static changeMultipleRows = (rows: RowType[], changedIndex: number, key: string, newValues: any[]): RowType[] => {
    const rightSideIndex = newValues.length + changedIndex;
    const [leftSide, rowsToChange, rightSide] = [
      rows.slice(0, changedIndex),
      rows.slice(changedIndex, rightSideIndex),
      rows.slice(rightSideIndex),
    ];
    rowsToChange.forEach((row, index) => (row[key] = newValues[index]));

    return [...leftSide, ...rowsToChange, ...rightSide];
  };

  static generateName = (columns: number): string =>
    columns > 1 ? DEFAULT_COLUMN_NAME + ` ${columns}` : DEFAULT_COLUMN_NAME;

  static _toSnakeCase = (word: string): string => word.toLowerCase().split(' ').join('_');
}

export default EditableTableUtils;
