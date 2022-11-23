import { Grid } from '@material-ui/core';
import React from 'react';
import PercentageInput from 'Components/CompetitionConfigView/PercentageInput';

export const ResidentialRatio = props => {
  return (
    <>
      <Grid item xs={12} sm={6} md={4}>
        <PercentageInput
          label="Target residential usage"
          name="residential_ratio.desired_ratio"
          helperText="Target share of residential usage in %"
          value={props['residential_ratio.desired_ratio'] || ''}
          onChange={props.onChange}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4}>
        <PercentageInput
          label="Acceptable Deviation"
          name="residential_ratio.acceptable_deviation"
          helperText="Deviation within which the feature will score partially"
          value={props['residential_ratio.acceptable_deviation'] || ''}
          onChange={props.onChange}
        />
      </Grid>
    </>
  );
};
