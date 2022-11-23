import React from 'react';
import { Checkbox, MenuItem, Select, Tooltip } from '@material-ui/core';
import './dropdown.scss';

const MAX_OPTION_LENGTH = 25;

export type DropdownOption = { label: string; value: string | number | boolean };

const CroppedOption = ({ label }) => (
  <Tooltip title={label}>
    <div>{label.slice(0, MAX_OPTION_LENGTH)}...</div>
  </Tooltip>
);

// @TODO: Use react select instead of material ui to render this select
//@TODO: Value can be an array or a number, put that in a type somewhere
const Dropdown = ({
  options,
  value,
  onChange,
  className = '',
  multiple = false,
  renderValue = undefined,
  IconComponent = undefined,
  open = undefined,
  onClose = undefined,
}) => {
  const optionalProps: any = {
    renderValue,
    IconComponent,
    open,
    onClose,
  };
  return (
    <Select
      className={`common-dropdown ${className}`}
      autoWidth={true}
      MenuProps={{ classes: { list: `common-menu-list menu-list-${className}` } }}
      disableUnderline
      displayEmpty={true}
      value={value}
      multiple={multiple}
      onChange={onChange}
      inputProps={{ 'data-testid': 'dropdown' }}
      {...optionalProps}
    >
      {options.map(option => (
        <MenuItem key={`${option.value} - ${option.label}`} value={option.value}>
          {option.label && option.label.length > MAX_OPTION_LENGTH ? (
            <CroppedOption label={option.label} />
          ) : (
            <>
              {multiple && <Checkbox id={`checkbox-${option.value}`} checked={value && value.includes(option.value)} />}
              <div>{option.label}</div>
            </>
          )}
        </MenuItem>
      ))}
    </Select>
  );
};

export default Dropdown;
