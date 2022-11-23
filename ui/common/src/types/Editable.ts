import { SelectProps } from '@material-ui/core';
import { InputHTMLAttributes } from 'react';

export enum INPUT_TYPES {
  text = 'text',
  number = 'number',
  textarea = 'textarea',
  dropdown = 'dropdown',
}

export interface EditableProps {
  onSave: (value: string | number) => void;
  onCancel?: () => void;
  onMultipleCellsChange?: (values: string[]) => void;
  onRemove?: () => void;
  value: string | number;
  component?: 'th' | 'td';
  type?: INPUT_TYPES;
  editing?: boolean;
  inputProps?: Omit<InputHTMLAttributes<any>, 'onChange' | 'onKeyDown'>;
  options?: { label: string; value: string | number }[];
  dropdownProps?: SelectProps;
}
