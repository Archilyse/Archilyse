import { Grid, Typography } from '@material-ui/core';
import { NumberInput } from 'Components/CompetitionConfigView/NumberInput';
import React from 'react';

export function AreaRequirements(props) {
  return (
    <>
      {props.label ? (
        <Grid item xs={12}>
          <Typography component="h1" variant="subtitle2">
            {props.label}
          </Typography>
        </Grid>
      ) : null}
      <Grid item xs={4}>
        <NumberInput
          label="Small side"
          unit="m"
          name={props.names.smallSideName}
          value={props[props.names.smallSideName] || ''}
          inputProps={{ min: 0, step: 0.01, max: props[props.names.bigSideName] }}
          onChange={e => props.onChange(props.names.smallSideName, e.target.value)}
          helperText="Min length of the small side"
        />
      </Grid>
      <Grid item xs={4}>
        <NumberInput
          label="Big side"
          unit="m"
          name={props.names.bigSideName}
          value={props[props.names.bigSideName] || ''}
          inputProps={{ min: props[props.names.smallSideName], step: 0.01 }}
          onChange={e => props.onChange(props.names.bigSideName, e.target.value)}
          helperText="Min length of the big side"
        />
      </Grid>
      <Grid item xs={4}>
        <NumberInput
          label="Min area"
          unit="m2"
          name={props.names.areaName}
          value={props[props.names.areaName] || ''}
          onChange={e => props.onChange(props.names.areaName, e.target.value)}
          inputProps={{ min: 0, step: 0.01 }}
          helperText="Min area requirement"
        />
      </Grid>
    </>
  );
}
