import { InputAdornment, TextField } from '@material-ui/core';
import React from 'react';

const PercentageInput = props => {
  return (
    <TextField
      required
      autoComplete="off"
      fullWidth
      {...props}
      type="number"
      inputProps={{
        ...props.inputProps,
        min: 0,
        max: 100,
        step: 0.01,
      }}
      InputProps={{
        ...props.InputProps,
        endAdornment: <InputAdornment position="end">%</InputAdornment>,
      }}
      value={props.value * 100}
      onChange={e => props.onChange(props.name, Number(e.target.value) / 100)}
    />
  );
};

export default PercentageInput;
