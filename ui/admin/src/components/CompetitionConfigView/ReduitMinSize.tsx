import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function ReduitMinSize(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Reduit min area"
        name="min_reduit_size"
        unit="m2"
        inputProps={{ min: 0, step: 0.01 }}
        value={props.min_reduit_size || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        helperText="Minimum area requirement for storage areas"
      />
    </Grid>
  );
}
