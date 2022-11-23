import React, { ReactNode } from 'react';
import { FlatDeviationResponseType } from '../../../../common/types';
import CompetitionConfigurationTableRow from './CompetitionConfigurationTableRow';
import './competitionConfigurationTable.scss';

export type CompetitionConfigurationTableHeaderType<T> = {
  key: keyof T;
  label: string;
  className?: string;
};

export type CompetitionConfigurationTableErrors = {
  apartment_type: string | null;
};

type Props<T = void> = {
  data: T[];
  errors: CompetitionConfigurationTableErrors[];
  loading?: ReactNode;
  extraHeaders?: CompetitionConfigurationTableHeaderType<T>[];
  onChange?: (newData: T[]) => void;
  ghostRow?: T;
};

const INITIAL_GHOST_ROW: FlatDeviationResponseType = {
  apartment_type: 1,
  percentage: null,
};

function CompetitionConfigurationTable<T extends FlatDeviationResponseType>({
  data = [],
  errors,
  loading,
  extraHeaders = [],
  onChange,
  ghostRow = INITIAL_GHOST_ROW as T,
}: Props<T>): JSX.Element {
  const handleOnChange = (indexToUpdate: number) => (newRow: T) => {
    if (data[indexToUpdate] === undefined) {
      handleOnAdd(newRow);
      return;
    }
    const updated = data.map((row, index) => (index === indexToUpdate ? newRow : row));

    onChange(updated);
  };

  const handleOnAdd = (newRow: T) => {
    onChange([...data, newRow]);
  };

  const handleOnRemove = (indexToRemove: number) => () => {
    const updated = data.filter((_, index) => index !== indexToRemove);
    onChange(updated);
  };

  return (
    <table className="flat-deviation-table">
      <thead>
        <tr>
          <th className="apartment-type">Apartment type</th>
          {extraHeaders.map(header => (
            <th key={header.key as string} className={header.className}>
              {header.label}
            </th>
          ))}
          <th className="percentage">%</th>
        </tr>
      </thead>
      <tbody>
        {loading ? (
          <tr>
            <td colSpan={2 + extraHeaders.length}>{loading}</td>
          </tr>
        ) : (
          [...data, ghostRow].map((row, index) => (
            <CompetitionConfigurationTableRow
              key={index}
              row={row}
              error={errors[index]}
              extraHeaders={extraHeaders.map(header => header.key)}
              onChange={handleOnChange(index)}
              onRowChange={index === data.length ? handleOnAdd : handleOnRemove(index)}
              mode={index === data.length ? 'creating' : 'editing'}
            />
          ))
        )}
      </tbody>
    </table>
  );
}

export default CompetitionConfigurationTable;
