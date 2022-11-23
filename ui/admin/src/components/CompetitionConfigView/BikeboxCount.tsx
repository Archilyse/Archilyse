import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function MinBikeBoxCount(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Bike boxes min count"
        name="bikes_boxes_count_min"
        unit=""
        value={props.bikes_boxes_count_min || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        inputProps={{ min: 0, step: 1 }}
        helperText="Minimum number of bike boxes for the entire project"
      />
    </Grid>
  );
}
