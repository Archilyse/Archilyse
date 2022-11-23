import React, { useState } from 'react';
import cn from 'classnames';
import { Editable, Icon, INPUT_TYPES } from 'archilyse-ui-components';
import { Tooltip } from '@material-ui/core';
import { getSafePercents } from '../utils';
import { FlatDeviationResponseType } from '../../../../common/types';
import { CompetitionConfigurationTableErrors } from './CompetitionConfigurationTable';

type ModeType = 'creating' | 'editing';

type Props<T = void> = {
  row: T & FlatDeviationResponseType;
  error: CompetitionConfigurationTableErrors;
  extraHeaders?: (keyof T)[];
  onChange: (newRow: T | null) => void;
  onRowChange: (newRow: T) => void;
  mode?: ModeType;
};

const ADD_REMOVE_ICON_STYLE = {
  width: 20,
  height: 20,
  fontSize: 20,
  marginLeft: 0,
  marginRight: 5,
};

const ERROR_COLOR = '#f76565';

const prettyCellValue = value => (value === null ? '—' : value);

const getOptionsByCurrentMode = (mode: ModeType) => {
  if (mode === 'creating') {
    return {
      cellClassName: 'new-value',
      iconName: 'add_circle_outline_rounded',
      rowButtonAriaLabel: 'add',
      inputAriaLabel: 'ghost',
    };
  }
  if (mode === 'editing') {
    return {
      iconName: 'remove_circle_outline_rounded',
      rowButtonAriaLabel: 'remove',
      inputAriaLabel: 'real',
    };
  }
};

function CompetitionConfigurationTableRow<T>({
  row,
  error,
  extraHeaders = [],
  mode = 'creating',
  onChange,
  onRowChange,
}: Props<T>): JSX.Element {
  const [editing, setEditing] = useState<keyof typeof row>(null);

  const closeEditing = () => {
    setEditing(null);
  };

  const handleOnSave = (field: keyof typeof row) => (newValue: string | number) => {
    if (field === 'percentage') {
      onChange({ ...row, [field]: Number(newValue) / 100 });
    } else {
      onChange({ ...row, [field]: Number(newValue) });
    }

    closeEditing();
  };

  const handleAddOrRemove = () => {
    onRowChange(row);
  };

  const { cellClassName, iconName, rowButtonAriaLabel, inputAriaLabel } = getOptionsByCurrentMode(mode);
  const [percentage, percentageValue] = getSafePercents(row.percentage);
  const firstCellWidth = extraHeaders.length > 0 ? undefined : '80%';

  return (
    <tr>
      <td className={cn('apartment-type', cellClassName)} style={{ width: firstCellWidth }}>
        <span>
          <button onClick={handleAddOrRemove} aria-label={rowButtonAriaLabel}>
            <Icon style={ADD_REMOVE_ICON_STYLE}>{iconName}</Icon>
          </button>
          Apartment type
          <Editable
            value={row.apartment_type}
            onSave={handleOnSave('apartment_type')}
            editing={editing === 'apartment_type'}
            onCancel={closeEditing}
            type={INPUT_TYPES.number}
            inputProps={{
              className: 'flat-deviation-input',
              step: 0.5,
              min: 1,
              max: 7,
            }}
          >
            <span
              className="apartment-type-editable editable-cell"
              onClick={() => setEditing('apartment_type')}
              role="button"
              aria-label={`apartment-type-${inputAriaLabel}`}
            >
              {row.apartment_type}
            </span>
            {Boolean(error?.apartment_type) && (
              <Tooltip title={error.apartment_type} arai-label={error.apartment_type}>
                <span role="alert" arai-label="error">
                  <Icon style={{ color: ERROR_COLOR, fontSize: 20 }}>error_outlined</Icon>
                </span>
              </Tooltip>
            )}
          </Editable>
        </span>
      </td>
      {extraHeaders.map(header => (
        <td key={header as string} className={cellClassName}>
          <span>
            <Editable
              value={Number(row[header])}
              onSave={handleOnSave(header)}
              editing={editing === header}
              onCancel={closeEditing}
              type={INPUT_TYPES.number}
              inputProps={{
                className: 'flat-deviation-input',
                min: 0,
                max: 100,
              }}
            >
              <span
                className="editable-cell"
                onClick={() => setEditing(header)}
                role="button"
                aria-label={`${header}-${inputAriaLabel}`}
              >
                {prettyCellValue(row[header])}
              </span>
            </Editable>
          </span>
        </td>
      ))}
      <td className={cn('percentage', cellClassName)}>
        <span>
          <Editable
            value={percentageValue}
            onSave={handleOnSave('percentage')}
            editing={editing === 'percentage'}
            onCancel={closeEditing}
            type={INPUT_TYPES.number}
            inputProps={{
              className: 'flat-deviation-input',
              step: 0.1,
              min: 0,
              max: 100,
            }}
          >
            <span
              className="editable-cell"
              onClick={() => setEditing('percentage')}
              role="button"
              aria-label={`percentage-${inputAriaLabel}`}
            >
              {percentage}
            </span>
          </Editable>
        </span>
      </td>
    </tr>
  );
}

export default CompetitionConfigurationTableRow;
