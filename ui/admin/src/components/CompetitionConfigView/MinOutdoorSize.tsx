import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function MinOutdoorSize(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="ANF per apt"
        name="min_outdoor_area_per_apt"
        unit="m2"
        inputProps={{ min: 0, step: 0.01 }}
        value={props.min_outdoor_area_per_apt || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        helperText="Total Outdoor minimum area desired per apt"
      />
    </Grid>
  );
}
