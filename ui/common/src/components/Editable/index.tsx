import { MenuItem, Select } from '@material-ui/core';
import React, { useEffect, useRef, useState } from 'react';
import { EditableProps, INPUT_TYPES } from '../../types';
import { useOnClickOutside } from '../../hooks';

const EXIT_KEY = 'Enter';

const Editable = ({
  onSave,
  onCancel = () => {},
  onMultipleCellsChange,
  value,
  type = INPUT_TYPES.text,
  editing: editingByDefault = false,
  inputProps,
  dropdownProps = {},
  options = [],
  children,
}: React.PropsWithChildren<EditableProps>): JSX.Element => {
  const [editing, setEditing] = useState(editingByDefault);
  const [innerValue, setInnerValue] = useState<string | number>(value || '');

  const inputRef = useRef<HTMLTextAreaElement | HTMLInputElement>();
  const exitEditingMode = () => {
    setEditing(false);

    handleSave();
  };

  useOnClickOutside(inputRef, exitEditingMode);

  const handleSave = () => {
    if (inputProps && (innerValue < inputProps.min || innerValue > inputProps.max)) {
      setInnerValue(value); // restore to initial value
      onCancel();
    } else {
      onSave(innerValue);
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
    if (type === INPUT_TYPES.number && isNaN(Number(event.target.value))) {
      return;
    }

    const newValue = event.target.value;

    const multipleValues = newValue.split('\n');
    if (onMultipleCellsChange && multipleValues.length > 1) {
      onMultipleCellsChange(multipleValues);
      setInnerValue(multipleValues[0]);
      setEditing(false);
    } else {
      setInnerValue(newValue);
    }
  };

  const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = event.target.value;

    setInnerValue(newValue);
    onSave(newValue);
  };

  const handleSelectClose = () => {
    setEditing(false);
    onCancel();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === EXIT_KEY) {
      exitEditingMode();
    }
  };

  useEffect(() => {
    setEditing(editingByDefault);
  }, [editingByDefault]);

  useEffect(() => {
    const isInputLoaded = Boolean(inputRef.current);
    if (editing && isInputLoaded) {
      inputRef.current.select();
    }
  }, [editing]);

  useEffect(() => {
    setInnerValue(value);
  }, [value]);

  const renderInput = () => {
    if (type === INPUT_TYPES.dropdown) {
      return (
        <Select
          value={innerValue}
          onChange={handleSelectChange}
          open={editing}
          onClose={handleSelectClose}
          onKeyDown={handleKeyDown}
          {...dropdownProps}
        >
          {options.map(option => (
            <MenuItem key={option.label + option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      );
    }

    if (type === INPUT_TYPES.textarea) {
      return (
        <textarea
          ref={ref => (inputRef.current = ref)}
          value={innerValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={1}
          className={inputProps.className}
          name={inputProps.name}
        />
      );
    }

    return (
      <input
        ref={ref => (inputRef.current = ref)}
        value={innerValue}
        type={type}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        {...inputProps}
      />
    );
  };

  return <>{editing ? renderInput() : children}</>;
};

export default Editable;
