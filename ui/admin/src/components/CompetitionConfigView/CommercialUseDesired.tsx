import { Checkbox, FormControlLabel, Grid } from '@material-ui/core';
import React from 'react';

export function CommercialUseDesired(props) {
  return (
    <>
      <Grid item xs={12}>
        <FormControlLabel
          label="Commercial use desired"
          control={
            <Checkbox
              checked={props.commercial_use_desired || false}
              color="primary"
              name="commercial_use_desired"
              onChange={e => props.onChange(e.target.name, e.target.checked)}
            />
          }
        />
      </Grid>
    </>
  );
}
