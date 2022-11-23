import { Grid } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function HNFRequirement(props) {
  return (
    <Grid item xs={12} sm={6}>
      <NumberInput
        label="Total HNF desired for the project"
        name="total_hnf_req"
        unit="m2"
        inputProps={{ min: 1, step: 0.01 }}
        value={props.total_hnf_req || ''}
        onChange={e => props.onChange(e.target.name, e.target.value)}
        helperText=""
      />
    </Grid>
  );
}
