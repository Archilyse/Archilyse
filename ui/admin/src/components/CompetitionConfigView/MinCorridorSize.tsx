import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function MinCorridorSize(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Minimum corridor size"
        name="min_corridor_size"
        unit="m"
        value={props.min_corridor_size || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        inputProps={{ min: 0, step: 0.01 }}
        helperText="Minimum diameter to ensure navigability for wheelchair users"
      />
    </Grid>
  );
}
