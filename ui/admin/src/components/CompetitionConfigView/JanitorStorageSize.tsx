import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function JanitorStorageSize(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Storage min area"
        name="janitor_storage_min_size"
        unit="m2"
        value={props.janitor_storage_min_size || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        inputProps={{ min: 0, step: 0.01 }}
        helperText="Minimum area requirement of the biggest janitor storeroom"
      />
    </Grid>
  );
}
