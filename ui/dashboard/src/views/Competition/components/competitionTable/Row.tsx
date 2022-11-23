import React from 'react';
import cn from 'classnames';
import useExpandable from '../useExpandable';
import TableUtils from './TableUtils';

type Props = {
  id: string;
  values: any[];
  getCellValue: (currentCell: any, index: number) => any;
  getRowValues: () => number[];
  renderCell: (score: any, index: number, className: string) => JSX.Element;
  renderLabel: (expandedProps: { expanded: boolean; onExpand: (isClosing: boolean) => void }) => JSX.Element;
};

const Row = ({
  id,
  values,
  getCellValue,
  getRowValues,
  renderCell,
  renderLabel,
  children,
}: React.PropsWithChildren<Props>): JSX.Element => {
  const { expanded, onExpand } = useExpandable(id);

  const _renderCell = (score: any, index: number) => {
    const currentValue = getCellValue(score, index);
    const rowValues = getRowValues();
    const isMaxValue = TableUtils.isMaxValue(currentValue, rowValues);

    const className = cn('cell', { bold: isMaxValue });

    return renderCell(score, index, className);
  };

  return (
    <>
      <tr>
        {renderLabel({ expanded, onExpand: children && onExpand })}
        {values.map(_renderCell)}
      </tr>
      {expanded && children}
    </>
  );
};

export default Row;
