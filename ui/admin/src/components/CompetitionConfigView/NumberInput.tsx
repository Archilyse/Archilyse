import { InputAdornment, TextField } from '@material-ui/core';
import React from 'react';

export function NumberInput(props) {
  return (
    <TextField
      fullWidth
      required
      autoComplete="off"
      {...props}
      type="number"
      InputProps={{
        ...props.InputProps,
        endAdornment: <InputAdornment position="end">{props.unit}</InputAdornment>,
      }}
    />
  );
}
