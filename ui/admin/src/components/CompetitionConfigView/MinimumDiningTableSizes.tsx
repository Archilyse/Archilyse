import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function MinimumDiningTableSizes(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Dining table SMALL side"
        name="dining_area_table_min_small_side"
        unit=""
        value={props.dining_area_table_min_small_side || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        inputProps={{ min: 0, step: 0.5 }}
        helperText="Requirement for the SMALLER side of the Dining table"
      />
      <NumberInput
        label="Dining table BIG side"
        name="dining_area_table_min_big_side"
        unit=""
        value={props.dining_area_table_min_big_side || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        inputProps={{ min: 0, step: 0.5 }}
        helperText="Requirement for the BIGGER side of the Dining table"
      />
    </Grid>
  );
}
